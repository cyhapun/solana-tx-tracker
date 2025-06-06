import requests
from constants import HELIUS_RPC, TOKEN_LIST_URL, TOKEN_SYMBOL_MAP
import pytz
from datetime import datetime
import json
import traceback

def load_token_symbols():
    global TOKEN_SYMBOL_MAP
    try:
        response = requests.get(TOKEN_LIST_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        for token in data['tokens']:
            TOKEN_SYMBOL_MAP[token['address']] = token['symbol']
    except requests.exceptions.RequestException as e:
        print(f"[!] Không thể tải danh sách symbol token: {e}")
    except json.JSONDecodeError:
        print("[!] Lỗi giải mã JSON từ danh sách token.")

def get_sol_balance(address):
    try:
        res = requests.post(HELIUS_RPC, json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [address]
        }, timeout=10).json()
        lamports = res.get("result", {}).get("value", 0)
        return lamports / 1e9
    except requests.exceptions.RequestException as e:
        print(f"[!] Lỗi khi lấy số dư SOL: {e}")
        return 0

def get_sol_tokens(address):
    balances = {}
    try:
        res = requests.post(HELIUS_RPC, json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [address, {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"}, {"encoding": "jsonParsed"}]
        }, timeout=10).json()
        
        token_list = res.get("result", {}).get("value", [])
        for token_account_info in token_list:
            try:
                parsed_info = token_account_info.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
                if not parsed_info:
                    continue
                
                mint = parsed_info.get("mint")
                token_amount_info = parsed_info.get("tokenAmount", {})
                amount_raw = token_amount_info.get("amount")
                decimals = token_amount_info.get("decimals")

                if amount_raw is None or decimals is None:
                    continue
                
                amount = int(amount_raw)
                if amount == 0:
                    continue
                
                symbol = TOKEN_SYMBOL_MAP.get(mint, "Unknown")
                readable_amount = amount / (10 ** decimals)
                
                display_key = f"{symbol} ({mint[:6]}...{mint[-4:]})"
                if display_key in balances:
                     balances[display_key] += readable_amount
                else:
                    balances[display_key] = readable_amount
            except Exception:
                continue
    except requests.exceptions.RequestException as e:
        print(f"[!] Lỗi khi lấy danh sách token: {e}")
    except Exception as e:
        print(f"[!] Lỗi không xác định khi lấy token: {e}")
    return balances

def get_sol_transactions(address, limit=10):
    try:
        res = requests.post(HELIUS_RPC, json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [address, {"limit": limit}]
        }, timeout=10).json()
        sigs = res.get("result", [])
        return [s["signature"] for s in sigs]
    except requests.exceptions.RequestException as e:
        print(f"[!] Lỗi khi lấy lịch sử giao dịch: {e}")
        return []

def get_transaction_details(signature):
    try:
        res = requests.post(HELIUS_RPC, json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [signature, {"encoding": "jsonParsed", "commitment": "finalized", "maxSupportedTransactionVersion": 0}]
        }, timeout=15)

        if res.status_code != 200:
            print(f"[!] Lỗi RPC ({res.status_code}) khi lấy chi tiết tx {signature}: {res.text}")
            return (None, 0, "Không xác định", "Lỗi RPC", [], [], [], [], [], [])

        res_json = res.json()
        if "error" in res_json:
            print(f"[!] RPC trả về lỗi cho tx {signature}: {res_json['error']}")
            return (None, 0, "Không xác định", "Lỗi RPC Data", [], [], [], [], [], [])

        result = res_json.get("result", {})
        if not result:
             print(f"[!] Không tìm thấy kết quả cho giao dịch {signature}. Có thể chưa finalized hoặc không tồn tại.")
             return (None, 0, "Không xác định", "Không có kết quả", [], [], [], [], [], [])

        slot = result.get("slot", "Không xác định")
        meta = result.get("meta", {})
        fee = meta.get("fee", 0) / 1e9
        block_time = result.get("blockTime", None)
        
        utc = pytz.UTC
        block_time_str = (datetime.fromtimestamp(block_time, tz=utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                          if block_time else "Không xác định")
        
        err = meta.get("err", None)
        status = "Thành công" if err is None else f"Thất bại ({err})"
        
        transaction_message = result.get("transaction", {}).get("message", {})
        account_keys_raw = transaction_message.get("accountKeys", [])
        
        account_keys = []
        if account_keys_raw:
            if isinstance(account_keys_raw[0], str) :
                header = transaction_message.get("header", {})
                num_signer_accounts = header.get("numRequiredSignatures", 0)
                for i, pk_str in enumerate(account_keys_raw):
                    account_keys.append({
                        "pubkey": pk_str,
                        "signer": i < num_signer_accounts,
                        "writable": True 
                    })
            elif isinstance(account_keys_raw[0], dict):
                account_keys = account_keys_raw

        pre_balances = meta.get("preBalances", [])
        post_balances = meta.get("postBalances", [])
        instructions = transaction_message.get("instructions", [])
        inner_instructions = meta.get("innerInstructions", [])
        token_balance_changes = meta.get("tokenBalanceChanges", [])
        
        return (slot, fee, block_time_str, status, account_keys, pre_balances, post_balances, instructions, inner_instructions, token_balance_changes)
    except requests.exceptions.RequestException as e:
        print(f"[!] Lỗi mạng khi lấy chi tiết giao dịch {signature}: {e}")
    except Exception as e:
        print(f"[!] Lỗi không xác định khi lấy chi tiết giao dịch {signature}: {e}")
        traceback.print_exc()
    return (None, 0, "Không xác định", "Lỗi Exception", [], [], [], [], [], [])

def analyze_solana_wallet(address):
    print(f"\n[+] Phân tích ví Solana: {address} (https://solscan.io/account/{address})")
    sol = get_sol_balance(address)
    print("Thông tin ví:")
    print(f"[+] Số dư SOL (Native SOL): {sol:.8f}")

    tokens = get_sol_tokens(address)
    if tokens:
        print("[+] Token đang nắm giữ:")
        for sym_and_mint, val in tokens.items():
            print(f"  - {sym_and_mint}: {val:.6f}")
    else:
        print("[!] Không phát hiện token nào hoặc có lỗi khi lấy token.")

    txs = get_sol_transactions(address)
    if txs:
        print("\n[+] Giao dịch gần đây (tối đa 10):")
        for sig in txs:
            print(f"  - TxHash: {sig} (https://solscan.io/tx/{sig})")
    else:
        print("[!] Không có giao dịch nào hoặc có lỗi khi lấy lịch sử giao dịch.")