# Validator Prototype Production Readiness Gaps

This document outlines the major work items needed to evolve the Python validator prototype toward Solana mainnet compatibility.

## Consensus and Fork Choice
- Implement vote account handling, Tower BFT rules, and fork selection based on supermajority stake.
- Add blockstore, replay stage, and leader schedule derivation to manage forks and slot progression.

## Proof of History and Block Production
- Replace the placeholder PoH hasher with a verifiable PoH recorder and tick scheduling.
- Integrate PoH with banking and shred production so slots can be produced, broadcast, and replayed.

## Banking Runtime
- Introduce an accounts database with rent/fee accounting, sysvars, and program execution via a runtime (BPF emulation or bindings).
- Enforce blockhash/nonce expiration, durable nonces, and fee rate governance consistent with upstream.

## Transaction Verification
- Parse full Solana wire transactions, including message layouts, account metas, and program instructions.
- Perform ed25519 signature verification over canonical messages and validate recent blockhashes against the ledger.

## Networking and Data Plane
- Replace ad-hoc UDP gossip with CRDS-based gossip, pull requests/responses, and signature verification of contact info.
- Add QUIC-based TPU/TVU data plane, turbine-style shred dissemination, retransmit/repair, and QoS.

## RPC and Client Compatibility
- Implement the Solana JSON-RPC surface (sendTransaction, getBlock, getProgramAccounts, commitment levels, websockets).
- Support snapshot download/restore paths and bank/ledger commitments for accurate RPC responses.

## Persistence and Bootstrap
- Persist the ledger and snapshots to disk, with restart and snapshot fetch capabilities.
- Add snapshot packaging, incremental snapshots, and state verification on startup.

## Security and Operations
- Manage validator, vote, and stake keypairs securely; support TLS/identity validation for gossip and data plane peers.
- Add metrics, logging, and health checks; include configuration for rate limits and DoS protections.

## Testing and Tooling
- Provide integration tests against solana-test-validator, wire-format compatibility tests, and banking runtime correctness suites.
- Benchmark performance under TPU load and transaction replay to guide optimization work.

### Implemented helpers
- `validator_py.testing` ships wire-format parsing checks, banking runtime verification, an in-process validator smoke test, and a TPU ingress benchmark to validate the prototype quickly.
