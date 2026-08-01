# Agent context design

The repository context follows current OpenAI prompt guidance without pinning an application
model, SDK, or API behavior:

- lead with the required outcome, then add only context that can change the result;
- make output expectations and the few material boundaries explicit;
- state durable organization instructions once at the repository root;
- load module architecture, contracts, commands, and skills only when their scope applies;
- keep tool authority narrow, descriptions precise, and external/destructive approval boundaries
  unambiguous; and
- validate prompt/context changes on representative repository tasks instead of assuming that
  more instructions improve behavior.

Official references reviewed for this materialization:

- https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6
- https://learn.chatgpt.com/docs/prompting

These references govern context structure only. Reva standards, tracked source, contracts, CI,
and explicit user approvals remain authoritative for product and engineering behavior.
