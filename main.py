import asyncio
from solana_client import load_token_symbols, analyze_solana_wallet
from transaction_monitor import track_sol_tx_websocket
from constants import API_KEY

def main():
    if API_KEY == "YOUR_API_KEY":
        print("[!] Vui lòng cập nhật API_KEY trong file constants.py trước khi chạy chương trình.")
        return
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
    finally:
        try:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()
        except Exception as e:
            print(f"[!] Lỗi khi dọn dẹp: {e}")
        print("[~] Chương trình kết thúc.")

if __name__ == "__main__":
    main()
