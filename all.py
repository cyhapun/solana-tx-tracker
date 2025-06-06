import asyncio
import requests
import json
import websockets
import base58
import struct
from datetime import datetime, timedelta
import pytz
import traceback

API_KEY = "YOUR_API_KEY"
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

def decode_memo_data(data_base58):
    try:
        decoded_bytes = base58.b58decode(data_base58)
        if decoded_bytes and (decoded_bytes[0] < len(decoded_bytes) -1) and all(0x20 <= b <= 0x7E or b in [0x0A, 0x0D, 0x09] for b in decoded_bytes[1:1+decoded_bytes[0]]):
            try:
                return f"Memo (có thể): {decoded_bytes[1:1+decoded_bytes[0]].decode('utf-8', errors='replace')}"
            except: pass
        return f"Memo: {decoded_bytes.decode('utf-8', errors='replace')}"
    except Exception:
        return f"Dữ liệu Memo (không phải UTF-8 hợp lệ): {data_base58}"

def decode_compute_budget_data(data_base58):
    try:
        data_bytes = base58.b58decode(data_base58)
        if not data_bytes: return "Dữ liệu ComputeBudget rỗng"
        instruction_type = data_bytes[0]
        details = ""
        if instruction_type == 0 and len(data_bytes) >= 9:
            units = struct.unpack('<I', data_bytes[1:5])[0]
            additional_fee = struct.unpack('<I', data_bytes[5:9])[0]
            details = f"RequestUnitsDeprecated: units={units}, additional_fee={additional_fee}"
        elif instruction_type == 1 and len(data_bytes) >= 5:
            bytes_val = struct.unpack('<I', data_bytes[1:5])[0]
            details = f"RequestHeapFrame: {bytes_val} bytes"
        elif instruction_type == 2 and len(data_bytes) >= 5:
            limit = struct.unpack('<I', data_bytes[1:5])[0]
            details = f"SetComputeUnitLimit: {limit} units"
        elif instruction_type == 3 and len(data_bytes) >= 9:
            price = struct.unpack('<Q', data_bytes[1:9])[0]
            details = f"SetComputeUnitPrice: {price} microLamports/CU"
        else:
            details = f"Lệnh ComputeBudget không xác định (type {instruction_type}), data: {data_base58}"
        return details
    except Exception as e:
        return f"Không thể giải mã data ComputeBudget ({data_base58}): {e}"

def parse_single_instruction(instr, tx_account_keys, current_tracked_address, indent="  "):
    program_id_str = instr.get('programId', 'Không xác định ProgramId')
    program_name = PROGRAM_ID_MAP.get(program_id_str, program_id_str)
    
    print(f"{indent}Chương trình: {program_name}{f' ({program_id_str})' if program_name != program_id_str else ''}")

    instr_accounts_indices = instr.get('accounts', [])
    if instr_accounts_indices:
        print(f"{indent}  Tài khoản trong lệnh này:")
        for acc_idx in instr_accounts_indices:
            # Nếu acc_idx là địa chỉ wallet (string dài 32+ ký tự), hiển thị trực tiếp
            if isinstance(acc_idx, str) and len(acc_idx) > 32:
                acc_display_name = PROGRAM_ID_MAP.get(acc_idx, TOKEN_SYMBOL_MAP.get(acc_idx, acc_idx))
                is_tracked = " (Ví đang theo dõi)" if acc_idx == current_tracked_address else ""
                print(f"{indent}    - {acc_display_name}{f' ({acc_idx})' if acc_display_name!=acc_idx else ''}{is_tracked}")
                continue
                
            # Xử lý chỉ mục số như cũ
            try:
                acc_idx = int(acc_idx)
                if 0 <= acc_idx < len(tx_account_keys):
                    acc_pk_str = tx_account_keys[acc_idx].get('pubkey', str(acc_idx))
                    acc_display_name = PROGRAM_ID_MAP.get(acc_pk_str, TOKEN_SYMBOL_MAP.get(acc_pk_str, acc_pk_str))
                    is_tracked = " (Ví đang theo dõi)" if acc_pk_str == current_tracked_address else ""
                    print(f"{indent}    - {acc_display_name}{f' ({acc_pk_str})' if acc_display_name!=acc_pk_str else ''}{is_tracked} (Chỉ mục Tx: {acc_idx})")
                else:
                    print(f"{indent}    - Chỉ mục tài khoản nằm ngoài phạm vi: {acc_idx}")
            except (ValueError, TypeError):
                print(f"{indent}    - Không thể xử lý chỉ mục: {acc_idx}")

    if "parsed" in instr:
        parsed = instr["parsed"]
        print(f"{indent}  Loại lệnh  : {parsed.get('type', 'Không xác định type')}")
        print(f"{indent}  Chi tiết   :")
        info = parsed.get('info', {})
        if not info: print(f"{indent}    (Không có thông tin chi tiết)")
        for k, v in info.items():
            if k == "lamports":
                print(f"{indent}    {k:<15}: {v / 1e9:.8f} SOL")
            elif k == "amount" and isinstance(v, str) and v.isdigit():
                print(f"{indent}    {k:<15}: {v} (đơn vị nhỏ nhất của token)")
            elif k == "mint" and v in TOKEN_SYMBOL_MAP:
                print(f"{indent}    {k:<15}: {v} ({TOKEN_SYMBOL_MAP[v]})")
            else:
                print(f"{indent}    {k:<15}: {v}")
    else:
        # print(f"{indent}  (Helius không phân tích sẵn lệnh này, hiển thị thông tin thô nếu có)")
        data_b58 = instr.get('data')
        if program_id_str == "ComputeBudget111111111111111111111111111111":
            if data_b58:
                decoded_info = decode_compute_budget_data(data_b58)
                print(f"{indent}  Chi tiết Data: {decoded_info}")
            else:
                print(f"{indent}  (Không có trường 'data' cho ComputeBudget)")
        elif program_id_str == "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr":
            if data_b58:
                memo_content = decode_memo_data(data_b58)
                print(f"{indent}  Nội dung Memo: {memo_content}")
            else:
                print(f"{indent}  (Không có data cho lệnh Memo)")
        elif program_id_str == "AxiomxSitiyXyPjKgJ9XSrdhsydtZsskZTEDam3PxKcC":
            print(f"{indent}  (Program này có thể là router cho Pump.fun)")
            if data_b58:
                print(f"{indent}  Data (Base58): {data_b58}")
            else:
                print(f"{indent}  (Không có data cho lệnh này)")
        elif data_b58:
            print(f"{indent}  Data (Base58): {data_b58}")
            print(f"{indent}  (Chưa hỗ trợ phân tích sâu cho dữ liệu của program này)")
        else:
            print(f"{indent}  (Không có trường 'data' hoặc không hỗ trợ phân tích sâu cho program này)")

def parse_transaction_log(log_notification, tx_counter, last_time, address):
    if 'method' not in log_notification or log_notification['method'] != 'logsNotification':
        return
    print("\n[*] NHẬN THÔNG BÁO GIAO DỊCH MỚI TỪ Helius WebSocket. TIẾN HÀNH PHÂN TÍCH...")

    try:
        value = log_notification['params']['result']['value']
        signature = value['signature']
        current_time = datetime.now(pytz.UTC)

        time_diff_seconds = float('inf')
        if last_time[0] is not None:
            time_diff_seconds = (current_time - last_time[0]).total_seconds()

        if time_diff_seconds >= 1:
            if tx_counter[0] > 5 and time_diff_seconds < 2 :
                 print(f"\n[!!!] CẢNH BÁO CAO: {tx_counter[0]} giao dịch trong khoảng {time_diff_seconds:.2f} giây! Có thể là bot!\n")
            elif tx_counter[0] > 3 and time_diff_seconds < 1:
                 print(f"\n[!] CẢNH BÁO: {tx_counter[0]} giao dịch trong khoảng {time_diff_seconds:.2f} giây - Có thể là bot!\n")
            tx_counter[0] = 1
            last_time[0] = current_time
        else:
            tx_counter[0] += 1
            if tx_counter[0] > 5 :
                 print(f"\n[!!!] CẢNH BÁO CAO (tức thời): {tx_counter[0]} giao dịch rất nhanh! Có thể là bot!\n")

        (slot, fee, block_time_str, status, account_keys, 
         pre_balances, post_balances, instructions, 
         inner_instructions, token_balance_changes) = get_transaction_details(signature)

        if slot is None:
            print(f"[!] Bỏ qua phân tích cho {signature} do lỗi lấy chi tiết.")
            return

        new_balance_tracked_wallet = None
        for i, acc_info in enumerate(account_keys):
            if acc_info.get("pubkey") == address and i < len(post_balances):
                new_balance_tracked_wallet = post_balances[i] / 1e9
                break
        
        involved_program_ids = list(set([instr.get('programId') for instr in instructions]))
        tx_summary = ""
        if "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33ZrTM4" in involved_program_ids:
            tx_summary = "Swap/Định tuyến qua Jupiter Aggregator"
        elif "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA" in involved_program_ids or \
             "AxiomxSitiyXyPjKgJ9XSrdhsydtZsskZTEDam3PxKcC" in involved_program_ids :
            tx_summary = "Tương tác với Pump.fun"
        elif "metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s" in involved_program_ids:
            tx_summary = "Tương tác với Metaplex Token Metadata (NFT)"
        elif any(pid in PROGRAM_ID_MAP and ("Raydium" in PROGRAM_ID_MAP.get(pid, "") or "Orca" in PROGRAM_ID_MAP.get(pid, "") or "Serum" in PROGRAM_ID_MAP.get(pid, "")) for pid in involved_program_ids):
            tx_summary = "Tương tác với sàn DEX (Raydium/Orca/Serum)"

        print("\n" + "="*200)
        print(" "*80 + "CHI TIẾT GIAO DỊCH MỚI")
        print("="*200)
        print(f"TxHash       : {signature} (https://solscan.io/tx/{signature})")
        print(f"Slot         : {slot}")
        print(f"Block Time   : {block_time_str}")
        print(f"Trạng thái   : {status}")
        print(f"Phí giao dịch: {fee:.8f} SOL")
        if tx_summary != "":
            print(f"Tóm tắt giao dịch: {tx_summary}")
        if new_balance_tracked_wallet is not None:
            print(f"Số dư mới ví : {new_balance_tracked_wallet:.8f} SOL")

        print("\n" + " "*80 + "CÁC ĐỊA CHỈ LIÊN QUAN TRONG GIAO DỊCH (TOÀN BỘ TX)")
        print("-" * 200)
        print(f"{'STT':<4} {'Public Key':<44} {'Signer':<7} {'Writable':<8} {'Fee Payer':<10} {'Nhận diện'}")
        print("-" * 200)
        
        fee_payer_pk = ""
        if account_keys and account_keys[0].get("signer"):
            fee_payer_pk = account_keys[0].get("pubkey")

        for i, acc_info in enumerate(account_keys, 1):
            pk = acc_info.get("pubkey", "N/A")
            signer_val = acc_info.get("signer", False)
            writable_val = acc_info.get("writable", False)
            
            signer = "Có" if signer_val else "Không"
            writable = "Có" if writable_val else "Không"
            
            is_fee_payer_str = "Có" if pk == fee_payer_pk else "Không"
            
            acc_type_name = PROGRAM_ID_MAP.get(pk, TOKEN_SYMBOL_MAP.get(pk, "Ví/PDA/TokenAccount"))
            is_tracked = " (Ví đang theo dõi)" if pk == address else ""
            
            print(f"{i:<4} {pk:<44} {signer:<7} {writable:<8} {is_fee_payer_str:<10} {acc_type_name}{is_tracked} (https://solscan.io/account/{pk})")
        print("-" * 200)

        print("\n" + " "*80 + "SỐ DƯ SOL THAY ĐỔI TRƯỚC VÀ SAU GIAO DỊCH")
        print("-" * 200)
        print(f"{'STT':<4} {'Public Key':<44} {'Trước (SOL)':>15} {'Sau (SOL)':>15} {'Thay đổi (SOL)':>18}")
        print("-" * 200)
        for i, acc_info in enumerate(account_keys):
            pk = acc_info.get("pubkey")
            if i < len(pre_balances) and i < len(post_balances):
                pre = pre_balances[i] / 1e9
                post = post_balances[i] / 1e9
                delta = post - pre
                if abs(delta) > 1e-9:
                    is_tracked = " (Ví đang theo dõi)" if pk == address else ""
                    print(f"{i+1:<4} {pk:<44} {pre:15.8f} {post:15.8f} {delta:+18.8f}{is_tracked}")
        print("-" * 200)

        if token_balance_changes:
            print("\n" + " "*80 + "THAY ĐỔI SỐ DƯ TOKEN (SPL)")
            print("-" * 200)
            print(f"{'Chủ TK':<20} {'Mint':<25} {'Symbol':<10} {'Trước':>18} {'Sau':>18} {'Thay đổi':>10}")
            print("-" * 200)
            for change in token_balance_changes:
                owner = change.get('owner', 'N/A')[:10]+'...'
                mint = change.get('mint', 'N/A')
                token_symbol = TOKEN_SYMBOL_MAP.get(mint, mint[:6]+"...")
                
                pre_ui = change.get('preBalance',{}).get('uiTokenAmount',{}).get('uiAmountString', 'N/A')
                post_ui = change.get('postBalance',{}).get('uiTokenAmount',{}).get('uiAmountString', 'N/A')
                
                try:
                    delta_val = float(post_ui if post_ui != 'N/A' else 0) - float(pre_ui if pre_ui != 'N/A' else 0)
                    delta_str = f"{delta_val:+.6f}" if abs(delta_val) > 1e-7 else "0"
                except (ValueError, TypeError):
                    delta_str = "N/A"

                is_owner_tracked = " (Ví theo dõi)" if change.get('owner') == address else ""

                print(f"{owner:<20}{is_owner_tracked} "
                      f"{mint[:10]+'...'+mint[-4:]:<25} "
                      f"{token_symbol:<10} "
                      f"{pre_ui:>18} "
                      f"{post_ui:>18} "
                      f"{delta_str:>10}")
            print("-" * 200)

        print("\n" + " "*80 + "CÁC LỆNH (INSTRUCTIONS)")
        print("-" * 200)
        for idx, instr in enumerate(instructions, 1):
            print(f"\nLệnh {idx}:")
            parse_single_instruction(instr, account_keys, address)
        print("-" * 200)
        
        if inner_instructions:
            print("\n" + " "*80 + "CÁC LỆNH CON (INNER INSTRUCTIONS)")
            print("-" * 200)
            for i_idx, inner_instr_set in enumerate(inner_instructions):
                original_instr_index = inner_instr_set.get('index')
                print(f"\n  Lệnh con cho Lệnh Gốc thứ: {original_instr_index + 1}")
                for j_idx, i_instr in enumerate(inner_instr_set.get('instructions',[]), 1):
                    print(f"\n  Lệnh con {j_idx} (của lệnh gốc {original_instr_index + 1}):")
                    parse_single_instruction(i_instr, account_keys, address, indent="    ")

        print("="*200)
        print(" "*80 + f"KẾT THÚC PHÂN TÍCH GIAO DỊCH")
        print("="*200, end="\n\n")
        print("Đang đợi giao dịch tiếp theo...")

    except Exception as e:
        print(f"[!!!] LỖI KHI PHÂN TÍCH LOG: {e}")
        traceback.print_exc()
        print("-" * 200)

async def track_sol_tx_websocket(address):
    max_retries = 5
    retry_delay = 5
    for attempt in range(max_retries):
        try:
            async with websockets.connect(HELIOUS_WS, ping_interval=20, ping_timeout=20) as ws:
                await ws.send(json.dumps({
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "logsSubscribe",
                    "params": [
                        {"mentions": [address]},
                        {"commitment": "finalized"}
                    ]
                }))
                
                print("[~] Đã gửi yêu cầu đăng ký theo dõi logs...")
                try:
                    confirmation_message = await asyncio.wait_for(ws.recv(), timeout=15)
                    confirmation_data = json.loads(confirmation_message)
                    if "result" in confirmation_data and isinstance(confirmation_data["result"], (int, str)):
                        print(f"[+] Đăng ký thành công! Subscription ID: {confirmation_data['result']}. Đang chờ giao dịch mới cho {address}...")
                    elif "error" in confirmation_data:
                        print(f"[!!!] LỖI ĐĂNG KÝ WebSocket: {confirmation_data['error']}. Vui lòng kiểm tra API key và địa chỉ ví.")
                        return
                    else:
                        print(f"[?] Phản hồi không xác định từ WebSocket sau khi đăng ký: {confirmation_message}. Tiếp tục theo dõi...")
                except asyncio.TimeoutError:
                    print("[!!!] LỖI: Không nhận được xác nhận đăng ký từ WebSocket sau 15 giây. Kiểm tra kết nối/API key.")
                    return
                except json.JSONDecodeError:
                    print(f"[!!!] LỖI: Không thể giải mã phản hồi xác nhận từ WebSocket: {confirmation_message}")
                    return
                except Exception as e_conf:
                    print(f"[!!!] LỖI bất ngờ khi chờ xác nhận đăng ký: {e_conf}")
                    return

                tx_counter = [0]
                last_time = [None] 
                while True:
                    try:
                        message = await asyncio.wait_for(ws.recv(), timeout=80)
                        data = json.loads(message)
                        if 'params' in data and 'subscription' in data['params'] and 'result' in data['params'] and isinstance(data['params']['result'], (int,str)):
                            continue
                        parse_transaction_log(data, tx_counter, last_time, address)
                    except asyncio.TimeoutError:
                        try:
                            await ws.ping()
                        except websockets.exceptions.ConnectionClosed:
                            print("[!] Kết nối WebSocket đã đóng khi đang ping. Thử kết nối lại...")
                            break 
                    except websockets.exceptions.ConnectionClosed as cc_err:
                        print(f"[!] Kết nối WebSocket đã đóng: {cc_err}. Thử kết nối lại...")
                        break
                    except Exception as e_recv:
                        print(f"[!] Lỗi khi nhận hoặc xử lý message WebSocket: {e_recv}")
                
                if ws.closed:
                    if attempt < max_retries -1:
                        print(f"Thử kết nối lại sau {retry_delay} giây... (Lần thử {attempt + 2}/{max_retries})")
                        await asyncio.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, 80)
                        continue
                    else:
                        print("[!] Đã đạt tối đa số lần thử kết nối lại. Dừng chương trình.")
                        return

        except websockets.exceptions.InvalidURI:
            print(f"[!] Lỗi: Địa chỉ WebSocket không hợp lệ: {HELIOUS_WS}")
            return
        except websockets.exceptions.WebSocketException as ws_e:
            print(f"[!] Lỗi khởi tạo WebSocket: {ws_e}")
            if attempt < max_retries -1:
                print(f"Thử kết nối lại sau {retry_delay} giây... (Lần thử {attempt + 2}/{max_retries})")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 80)
            else:
                print("[!] Đã đạt tối đa số lần thử kết nối lại WebSocket. Dừng chương trình.")
                return
        except Exception as e_main_ws:
            print(f"[!] Lỗi không xác định trong track_sol_tx_websocket: {e_main_ws}")
            traceback.print_exc()
            if attempt < max_retries -1:
                print(f"Thử kết nối lại sau {retry_delay} giây... (Lần thử {attempt + 2}/{max_retries})")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 80)
            else:
                print("[!] Đã đạt tối đa số lần thử kết nối lại. Dừng chương trình.")
                return
        else:
            break 

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

if __name__ == "__main__":
    print("="*200)
    print(" "*80 + "CHƯƠNG TRÌNH THEO DÕI VÀ PHÂN TÍCH GIAO DỊCH SOLANA")
    print("="*200 + "\n")

    load_token_symbols()
    addr_input = ""
    while not addr_input:
        addr_input = input("Nhập địa chỉ ví Solana cần theo dõi: ").strip()
        if not addr_input:
            print("[!] Địa chỉ ví không được để trống. Vui lòng nhập lại.")
            
    analyze_solana_wallet(addr_input)
    print("\n[~] Bắt đầu theo dõi giao dịch real-time (ấn Ctrl+C để thoát)...")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(track_sol_tx_websocket(addr_input))
    except KeyboardInterrupt:
        print("\n[x] Dừng theo dõi theo yêu cầu người dùng.")
    except Exception as e:
        print(f"\n[!!!] Lỗi không mong muốn ở cấp cao nhất: {e}")
        traceback.print_exc()
    finally:
        try:
            # Đóng tất cả các task đang chạy
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            # Chạy loop một lần nữa để các task được đóng đúng cách
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()
        except Exception as e:
            print(f"[!] Lỗi khi dọn dẹp: {e}")
        print("[~] Chương trình kết thúc.")