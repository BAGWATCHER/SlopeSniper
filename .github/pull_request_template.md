## Summary

-

## Testing

- [ ] `pytest`
- [ ] `ruff check mcp-extension/src tests`
- [ ] `python -m build mcp-extension`

## Safety checklist

- [ ] No private keys, wallet files, API keys, webhook URLs, or obfuscated secrets committed
- [ ] Trading behavior is conservative by default or requires explicit opt-in
- [ ] Wallet/signing/confirmation changes include tests or a clear manual test plan
- [ ] Docs updated for user-visible behavior changes
