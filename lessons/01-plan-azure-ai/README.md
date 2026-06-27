# Lesson 1 -- Choose Foundry services, models, and integration approach

Welcome! This is the hands-on demo for **Module 1** of the Microsoft Press video
course *Exam AI-103: Developing AI Apps and Agents on Azure*.

Module 1 is about **decisions**: which model, which Foundry service, which retrieval
method, and which agent building blocks fit the job. This demo makes the most
important of those decisions concrete.

## The experiment: a model bake-off

`model_bakeoff.py` sends the **same prompt** to two models you have deployed in
Microsoft Foundry -- a **flagship LLM** (for example, `gpt-5.1`) and a **small
language model** (for example, `phi-4`) -- and prints a side-by-side scoreboard of
**latency, token usage, and the answers**.

The point is not "which model is best." It is the durable AI-103 habit: **task fit
beats brand name.** You will watch the SLM come back faster and cheaper while the
flagship reasons a little deeper, and you will pick by the constraint in front of you.

## What you will need

- A **Microsoft Foundry** project.
- **Two model deployments** in that project: one flagship LLM and one small model.
- The **Azure CLI**, signed in with `az login` (auth is keyless -- no API keys).
- **Python 3.10+**.

## Setup

```bash
pip install -r requirements.txt
az login
# copy .env.example to .env and fill in your values (or set them as real env vars)
```

Your three settings (see `.env.example`):

| Variable | What it is |
|---|---|
| `FOUNDRY_PROJECT_ENDPOINT` | Foundry portal -> your project -> Overview -> Endpoint |
| `FLAGSHIP_DEPLOYMENT` | the deployment **name** of your flagship model (e.g. `gpt-5.1`) |
| `SLM_DEPLOYMENT` | the deployment **name** of your small model (e.g. `phi-4`) |

> Heads-up: `model=` in the SDK takes your **deployment name**, not the base model
> id. Routing by deployment name lets you swap the underlying model later without
> touching application code -- an AI-103 talking point in its own right.

## Run it

```bash
python model_bakeoff.py
python model_bakeoff.py --prompt "Summarize the CAP theorem in one sentence."
```

## What you will see (illustrative)

```
[FLAGSHIP LLM]  deployment = gpt-5.1
  latency : 1.84s    tokens: 28 in / 73 out
  answer  : ...

[SMALL MODEL (SLM)]  deployment = phi-4
  latency : 0.62s    tokens: 28 in / 61 out
  answer  : ...

Fastest response: SMALL MODEL (SLM) (phi-4) at 0.62s.
Takeaway: match the model to the workload...
```

## How this maps to the exam

This demo lives under **"Choose an appropriate model for each task, including LLMs,
small language models, multimodal models, and Foundry Tools."** When an exam stem
hands you a constraint -- lowest latency on an edge device, a tight budget, a simple
generative task -- the answer is usually the small model, not the flagship.

---
Part of the [AI-103 course repository](https://github.com/timothywarner-org/ai103) by Tim Warner.
