import asyncio
import websockets
import json
from constants import HELIOUS_WS, PROGRAM_ID_MAP, TOKEN_SYMBOL_MAP
from utils import parse_single_instruction
from solana_client import get_transaction_details
from datetime import datetime
import pytz
import traceback

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
            if tx_counter[0] > 3 and time_diff_seconds < 2 :
                 print(f"\n[!!!] CẢNH BÁO: {tx_counter[0]} giao dịch trong khoảng {time_diff_seconds:.2f} giây! Có thể là bot!\n")
            elif tx_counter[0] > 3 and time_diff_seconds < 1:
                 print(f"\n[!] CẢNH BÁO: {tx_counter[0]} giao dịch trong khoảng {time_diff_seconds:.2f} giây - Có thể là bot!\n")
            tx_counter[0] = 1
            last_time[0] = current_time
        else:
            tx_counter[0] += 1
            if tx_counter[0] > 3 :
                 print(f"\n[!!!] CẢNH BÁO: {tx_counter[0]} giao dịch rất nhanh! Có thể là bot!\n")

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