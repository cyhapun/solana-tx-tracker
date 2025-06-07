API_KEY = "463c8aa3-2f58-4b15-8890-943b47097a3c"
HELIUS_RPC = f"https://mainnet.helius-rpc.com/?api-key={API_KEY}"
HELIOUS_WS = f"wss://rpc.helius.xyz/?api-key={API_KEY}"
TOKEN_LIST_URL = "https://raw.githubusercontent.com/solana-labs/token-list/main/src/tokens/solana.tokenlist.json"
TOKEN_SYMBOL_MAP = {}
PROGRAM_ID_MAP = {
    "11111111111111111111111111111111": "System Program",
    "ComputeBudget111111111111111111111111111111": "Compute Budget Program",
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA": "SPL Token Program",
    "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL": "Associated Token Account Program",
    "Stake11111111111111111111111111111111111111": "Stake Program",
    "BPFLoader1111111111111111111111111111111111": "BPF Loader",
    "BPFLoader2111111111111111111111111111111111": "BPF Loader 2",
    "BPFLoaderUpgradeab1e11111111111111111111111": "Upgradeable BPF Loader",
    "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr": "Memo Program",
    "ZkTokenProof1111111111111111111111111111111": "ZK Token Proof Program",
    "Vote111111111111111111111111111111111111111": "Vote Program",
    "NamesLP1oM2KngRxCkq9bNCM3QFoYn7GEY8W2Vg3dAHT": "Solana Name Service",
    "Sysvar1111111111111111111111111111111111111": "Sysvar Program",
    "Secp256k1SigVerify11111111111111111111111111": "Secp256k1 Signature Verify Program",
    "Ed25519SigVerify111111111111111111111111111": "Ed25519 Signature Verify Program",
    "metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s": "Metaplex Token Metadata Program",
    "p1exdMJcjVao65QdewkaZRUnU6VPSXhusxknULred": "Metaplex Auction House Program",
    "cndy3Z4yapfJBmL3ShUp5exZKqR3z33thTzeAMxNava": "Metaplex Candy Machine v2 Program",
    "SW1TCH7qEPTdLsDHRgPuAbZyY1f8KecTq9nnCB7i4": "Switchboard Oracle Program",
    "srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX": "Serum DEX v3 Program",
    "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin": "Serum Swap Program",
    "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33ZrTM4": "Jupiter Aggregator v4 Program",
    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": "Raydium Liquidity Pool v4 Program",
    "PhoeNiXZ8ByJGLkxNfZRnkUfjvmuYqLR89jjFHGqdXY": "Phoenix Finance Program",
    "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc": "Whirlpools Program (Orca)",
    "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA": "Pump.fun AMM",
    "AxiomxSitiyXyPjKgJ9XSrdhsydtZsskZTEDam3PxKcC": "Axiom (Thường liên quan Pump.fun Router)",
    "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo": "Meteora DLMM Program",
    "MarBmsSgKXdrN1egZf5sqe1TMai9K1rChYNDJgjq7aD": "Marinade Staking Program",
    "worm2ZoG2kUd4vFXhvjh93UUH596ayRfgQ2MgjNMTc": "Wormhole Token Bridge Program",
}
