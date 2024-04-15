---
title: TokenTrace
summary: A backend tool and frontend user interface for visualizing SAE feature attribution scores
tags:
  - Deep Learning
date: "2024-04-14T00:00:00Z"

# Optional external URL for project (replaces project detail page).
external_link: ''

---

We build a tool to compute attribution scores with respect to next-token prediction loss for any user-submitted prompt, closely following the methodology described in [Sparse Feature Circuits](https://arxiv.org/abs/2403.19647). We also build an interactive frontend in Streamlit to aid visual inspection of interesting features. 

We apply our tool to a standard IOI prompt and use our tool to inspect the model's computation. Based on quick visual inspection, we find evidence that the early layers of the model construct multiple grammatically-plausible completions, and the middle-to-late layers filter these completions to select the most semantically likely one. We also find that more than half of the total attribution is captured by reconstruction error terms rather than SAE features. This could be due to inaccuracies in the attribution method, or due to intrinsic error in the trained SAEs. 

This project was done as part of the InterpVis hackathon, organised by Apart Research. It took place from April 13-14 at the London Initiative for Safe AI Headquarters. 

Our code is publicly available [here](https://github.com/interp-hack/token-trace).
Our final slide deck can be found [here](https://drive.google.com/file/d/1Io_79EvpBVHegHEWlRnwu8cHju1XgHB1/view?usp=sharing)