# OpenAI Independent Critic Adapter

This image is the provider implementation for the Story Engine v1.1 external Critic boundary.

It reads only the sealed files mounted by `run_external_critic_orchestrator.py`:

- `NASDAQ_CAFE_CRITIC_REQUEST`
- `NASDAQ_CAFE_CRITIC_BUNDLE`

and writes exactly one review JSON to:

- `NASDAQ_CAFE_CRITIC_REVIEW_OUT`

The adapter does not read the repository, does not receive Author scratch context, does not use web search or tools, and does not sign its own judgment. The outer trusted orchestrator validates the review and creates the Ed25519 attestation/receipt.

## Provider

The adapter uses the OpenAI Responses API with Structured Outputs. Default model:

`gpt-5.6`

Required environment:

`OPENAI_API_KEY`

Optional environment:

- `OPENAI_CRITIC_MODEL` — defaults to `gpt-5.6`
- `OPENAI_CRITIC_MAX_OUTPUT_TOKENS` — defaults to `12000`
- `OPENAI_CRITIC_TIMEOUT_SECONDS` — defaults to `180`

The Python SDK is pinned in `requirements.txt` so the release image can be built and then referenced by immutable container digest.

## Build

```bash
docker build -t nasdaq-cafe-openai-critic:local critic-adapters/openai
```

A production run must not use this mutable local tag. Publish the image through the chosen external registry and pass the immutable `image@sha256:<digest>` reference to the external Critic pipeline.

## Safety boundary

The adapter is deliberately not allowed to:

- fetch additional market facts;
- alter Expected / Actual / Gap;
- strengthen causal scope or confidence;
- create or apply Story patches;
- generate an Ed25519 signing key;
- sign or upgrade the production receipt;
- invoke GitHub Actions or Remotion.

A `revise` or `blocked` review is still a valid model result. The outer Story Engine gate decides whether production may continue.
