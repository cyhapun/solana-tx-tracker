import base58
import struct
from constants import TOKEN_SYMBOL_MAP, PROGRAM_ID_MAP

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
        for acc_idx in set(instr_accounts_indices):
            acc_display_name = PROGRAM_ID_MAP.get(acc_idx, TOKEN_SYMBOL_MAP.get(acc_idx, acc_idx))
            is_tracked = " (Ví đang theo dõi)" if acc_idx == current_tracked_address else ""
            print(f"{indent}    - {acc_display_name}{f' ({acc_idx})' if acc_display_name!=acc_idx else ''}{is_tracked}")
            continue
        
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