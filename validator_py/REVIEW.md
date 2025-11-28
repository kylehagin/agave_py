# Production-readiness review for `validator_py`

This review checks the implementation against the earlier roadmap areas and calls out major gaps that prevent a production-compatible Solana validator.

## Consensus / fork choice
- Fork choice now tracks Tower-inspired lockout votes and advances a rooted slot while still selecting the heaviest tip by cumulative stake. Safety rules such as slashing and replay-stage integration remain future work. 【F:validator_py/consensus.py†L23-L107】

## Proof of History and block production
- PoH entries now retain mixins from transaction signatures, emit per-tick entries, and include a verifier alongside leader-scheduled slot production. Leader rotation is round-robin over the configured schedule, but full leader selection and turbine/TVU alignment are still simplified. 【F:validator_py/poh.py†L17-L141】

## Banking/runtime
- The banking runtime now dispatches instructions through a program registry, supports SystemProgram create-account and transfer flows, accrues rent against data-bearing accounts, and exposes program registration hooks. CPI, stake/vote programs, and rent-governance remain unimplemented. 【F:validator_py/runtime.py†L35-L175】

## Transaction verification and ledger
- Blockhash validation now enforces a slot-based expiry horizon and snapshots persist the expiry queue alongside transaction statuses. Durable nonce account execution is still absent, and the ledger remains in-memory outside of snapshots. 【F:validator_py/ledger.py†L1-L145】

## Networking and data plane
- Networking continues to use the prototype UDP data plane; QUIC transport, turbine fanout with retransmit/repair windows, and stake-weighted peer selection are still required for production parity. 【F:validator_py/network.py†L16-L620】

## RPC and client compatibility
- The JSON-RPC surface remains limited; commitment levels, program account filtering, stake/vote APIs, and hardened websocket semantics are still pending. 【F:validator_py/rpc.py†L1-L400】

## Persistence, security, and operations
- Snapshot signing/versioning and per-slot integrity proofs are still TODO; network and RPC authentication/DoS protections need strengthening beyond existing rate limits. 【F:validator_py/persistence.py†L1-L148】【F:validator_py/operations.py†L1-L140】

## Testing and tooling
- Property/fuzz testing, performance regression checks, and cross-validation against a reference Solana cluster remain to be built atop the smoke harness. 【F:validator_py/testing.py†L1-L260】

## Overall status
Recent changes add lockout-aware consensus, PoH entry tracking, rent-accruing banking with program dispatch, and blockhash expiry enforcement. The prototype still lacks production-grade data plane, full runtime/program coverage, and hardened persistence/security; additional work is required before mainnet compatibility.
