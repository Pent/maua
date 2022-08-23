import os
import sys
from functools import partial

import numpy as np
import torch
import torch.nn as nn
from huggingface_hub import hf_hub_download
from omegaconf import OmegaConf
from torch import autocast

from ...prompt import TextPrompt
from .base import BaseDiffusionProcessor
from .latent import LatentDiffusion, load_model_from_config

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + "/../../submodules/k_diffusion")
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + "/../../submodules/stable_diffusion")
from ...submodules.k_diffusion import k_diffusion
from ...submodules.latent_diffusion.ldm.models.diffusion.ddim import DDIMSampler
from ...submodules.latent_diffusion.ldm.models.diffusion.plms import PLMSSampler


def get_model(checkpoint):
    if checkpoint in ["1.1", "1.2", "1.3", "1.4"]:
        version = checkpoint.replace(".", "-")
        ckpt = f"modelzoo/stable-diffusion-v{version}.ckpt"
        config = (
            os.path.abspath(os.path.dirname(__file__))
            + "/../../submodules/stable_diffusion/configs/stable-diffusion/v1-inference.yaml"
        )
        if not os.path.exists(ckpt):
            hf_hub_download(
                repo_id=f"CompVis/stable-diffusion-v-{version}-original",
                filename=f"sd-v{version}.ckpt",
                cache_dir="modelzoo/",
                force_filename=f"stable-diffusion-v{version}.ckpt",
                use_auth_token=True,
            )
    else:
        ckpt = checkpoint
        config = checkpoint.replace(".ckpt", ".yaml")
    return load_model_from_config(OmegaConf.load(config), ckpt)


class StableConditioning(torch.nn.Module):
    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, prompts):
        for prompt in prompts:
            if isinstance(prompt, TextPrompt):
                txt, _ = prompt()
                conditioning = self.model.get_learned_conditioning([txt])
                unconditional = self.model.get_learned_conditioning([""])
        return conditioning, unconditional


class StableDiffusion(LatentDiffusion):
    def __init__(
        self,
        cfg_scale=3,
        sampler="dpm_2",
        timesteps=100,
        model_checkpoint="1.4",
        ddim_eta=0,
        device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
    ):
        super(BaseDiffusionProcessor, self).__init__()

        self.model = get_model(model_checkpoint)
        self.image_size = self.model.image_size * 8

        self.conditioning = StableConditioning(self.model)
        self.cfg_scale = cfg_scale

        if sampler == "plms":
            sampler = PLMSSampler(self.model)
            sampler.make_schedule(ddim_num_steps=timesteps, ddim_eta=ddim_eta, verbose=False)
            self.sample_fn = sampler.plms_sampling
            self.original_num_steps = sampler.ddpm_num_timesteps
        elif sampler == "ddim":
            sampler = DDIMSampler(self.model)
            sampler.make_schedule(ddim_num_steps=timesteps, ddim_eta=ddim_eta, verbose=False)
            self.sample_fn = sampler.ddim_sampling
            self.original_num_steps = sampler.ddpm_num_timesteps
        else:
            self.model_wrap = k_diffusion.external.CompVisDenoiser(self.model)
            self.sigmas = self.model_wrap.get_sigmas(timesteps)
            self.sample_fn = getattr(k_diffusion.sampling, f"sample_{sampler}")
            self.original_num_steps = len(self.model.alphas_cumprod)

        self.device = device
        self.model = self.model.to(device)
        self.timestep_map = np.linspace(0, self.original_num_steps, timesteps + 1).round().astype(int)

    @torch.no_grad()
    def forward(self, img, prompts, start_step, n_steps=None, verbose=True):
        if not hasattr(self, "sigmas"):
            return super().forward(img, prompts, start_step, n_steps, verbose)
            # LatentDiffusion class supports plms and ddim, below does not
            # TODO make all classes support k_diffusion samplers!

        if n_steps is None:
            n_steps = start_step + 1
        start_step = len(self.sigmas) - start_step - 2

        cond, uncond = self.conditioning([p.to(img) for p in prompts])

        with autocast("cuda"), self.model.ema_scope():
            if start_step > 0:
                x = self.model.get_first_stage_encoding(self.model.encode_first_stage(img))
                x += torch.randn_like(x) * self.sigmas[start_step]
            else:
                x = torch.randn(
                    [img.shape[0], 4, img.shape[-2] // 8, img.shape[-1] // 8], device=img.device, dtype=img.dtype
                )
                x *= self.sigmas[0]

            shape = (x.shape[0], cond.shape[1], cond.shape[2])
            samples = self.sample_fn(
                partial(cfg_forward, model=self.model_wrap),
                x,
                self.sigmas[start_step : start_step + n_steps + 1],
                extra_args={"cond": cond.expand(shape), "uncond": uncond.expand(shape), "cond_scale": self.cfg_scale},
                disable=not verbose,
            )
            samples_out = self.model.decode_first_stage(samples)

        return samples_out.float()


def cfg_forward(x, sigma, uncond, cond, cond_scale, model):
    x_in = torch.cat([x] * 2)
    sigma_in = torch.cat([sigma] * 2)
    cond_in = torch.cat([uncond, cond])
    uncond, cond = model(x_in, sigma_in, cond=cond_in).chunk(2)
    return uncond + (cond - uncond) * cond_scale
