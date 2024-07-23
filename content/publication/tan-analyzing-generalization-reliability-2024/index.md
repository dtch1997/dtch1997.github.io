---
title: Analyzing the Generalization and Reliability of Steering Vectors
authors:
- Daniel Tan
- David Chanin
- Aengus Lynch
- Dimitrios Kanoulas
- Brooks Paige
- Adria Garriga-Alonso
- Robert Kirk
date: '2024-07-22'
publishDate: '2024-07-23T14:16:19.361903Z'
publication_types:
- manuscript
doi: 10.48550/arXiv.2407.12404
abstract: Steering vectors (SVs) are a new approach to efficiently adjust language
  model behaviour at inference time by intervening on intermediate model activations.
  They have shown promise in terms of improving both capabilities and model alignment.
  However, the reliability and generalisation properties of this approach are unknown.
  In this work, we rigorously investigate these properties, and show that steering
  vectors have substantial limitations both in- and out-of-distribution. In-distribution,
  steerability is highly variable across different inputs. Depending on the concept,
  spurious biases can substantially contribute to how effective steering is for each
  input, presenting a challenge for the widespread use of steering vectors. Out-of-distribution,
  while steering vectors often generalise well, for several concepts they are brittle
  to reasonable changes in the prompt, resulting in them failing to generalise well.
  Overall, our findings show that while steering can work well in the right circumstances,
  there remain many technical difficulties of applying steering vectors to guide models'
  behaviour at scale.
tags:
- Computer Science - Machine Learning
links:
- name: URL
  url: http://arxiv.org/abs/2407.12404
---
