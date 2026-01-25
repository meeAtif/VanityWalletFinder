import multiprocessing
import time
import os
import sys
import re
from datetime import datetime
from queue import Empty

# Third-party libraries
# bip_utils is highly optimized and uses coincurve/ecdsa
from bip_utils import (
    Bip39MnemonicGenerator, Bip39SeedGenerator,
    Bip44, Bip44Coins, Bip44Changes,
    Bip84, Bip84Coins,
    Bip39WordsNum
)
import colorama
from colorama import Fore, Style

# Initialize colorama
colorama.init()

# Constants
OUTPUT_DIR = "output"
BATCH_SIZE = 50  # Increased batch size slightly as we process 5 addrs per mnemonic

def check_criteria(address, patterns):
    """
    Check if address matches any of the patterns.
    patterns: dict of criteria
    Returns: match_type (str) or None, score (int)
    """
    # Starts with
    if 'starts_with' in patterns:
        for p in patterns['starts_with']:
            if address.startswith(p):
                return f"Starts with '{p}'", 10

    # Ends with
    if 'ends_with' in patterns:
        for p in patterns['ends_with']:
            if address.endswith(p):
                return f"Ends with '{p}'", 10

    # Contains
    if 'contains' in patterns:
        for p in patterns['contains']:
            if p in address:
                return f"Contains '{p}'", 8

    # Repeating characters
    if 'repeating' in patterns:
        min_repeats = patterns['repeating']
        loc = patterns.get('repeating_loc', 'any')
        
        # Regex for repeating characters
        # (.)\1{min_repeats-1}
        regex_pat = r'(.)\1{' + str(min_repeats - 1) + r',}'
        if loc == 'end':
            regex_pat += r'$'
            
        match = re.search(regex_pat, address)
        if match:
            found_seq = match.group(0)
            return f"{len(found_seq)} repeating chars '{found_seq[0]}'", 9

    return None, 0

def worker_process(network, patterns, result_queue, counter_queue):
    """
    Worker process to generate wallets and check patterns.
    Uses bip_utils for faster processing.
    """
    # Initialize generator
    # 12 words (128 bits entropy) is standard and faster
    mnemonic_gen = Bip39MnemonicGenerator()
    seed_gen = Bip39SeedGenerator
    
    while True:
        # Generate batch
        for _ in range(BATCH_SIZE):
            # Generate Mnemonic
            mnemonic_phrase = mnemonic_gen.FromWordsNumber(Bip39WordsNum.WORDS_NUM_12)
            seed_bytes = seed_gen(mnemonic_phrase).Generate()
            
            bip_obj_ctx = None
            
            # Create the Bip object based on network
            if network == 'ETH':
                # m/44'/60'/0'/0
                bip_obj_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
                
            elif network == 'BTC_LEGACY':
                # m/44'/0'/0'/0
                bip_obj_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
                
            elif network == 'BTC_SEGWIT':
                # m/84'/0'/0'/0
                bip_obj_ctx = Bip84.FromSeed(seed_bytes, Bip84Coins.BITCOIN)
            
            # Derive first 5 addresses: indices 0 to 4
            # We assume the path above is the account level or we step down to change level
            # Actually bip_utils FromSeed gives us the root. We usually need to traverse.
            # However, Bip44.FromSeed initiates with the default path for the coin if not specified? 
            # No, FromSeed returns a Bip44 object at depth 0 usually?
            # Let's verify: Bip44.FromSeed returns a wrapper. We should traverse to keys.
            
            # Bip44 default path for Ethereum: m/44'/60'/0'/0/0
            # For iteration, we want to go to the Change level (m/44'/60'/0'/0) and then iterate addresses
            
            # Optimization: 
            # Bip44/Bip84 classes automatically handle the hierarchy according to the spec.
            # Step 1: Purpose/Coin/Account/Change
            
            # Using Step-by-step for clarity and correctness:
            # acc_ctx = bip_obj_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
            
            # But the bip_obj_ctx returned by FromSeed is already the root.
            # Let's just use the automatic path derivation to the address index level if possible, 
            # or manually step down.
            
            # Helper to get to the address generator level
            if network == 'ETH':
                acc = bip_obj_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
            elif network == 'BTC_LEGACY':
                acc = bip_obj_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
            elif network == 'BTC_SEGWIT':
                # Bip84 structure is same: Purpose/Coin/Account/Change
                acc = bip_obj_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
            
            # Scan 5 addresses
            for i in range(5):
                addr_ctx = acc.AddressIndex(i)
                address = addr_ctx.PublicKey().ToAddress()
                
                # Check Pattern
                match_type, score = check_criteria(address, patterns)
                
                if match_type:
                    result = {
                        'address': address,
                        'mnemonic': mnemonic_phrase,
                        'path_index': i,
                        'type': match_type,
                        'score': score,
                        'timestamp': datetime.now().isoformat()
                    }
                    result_queue.put(result)
        
        # Update counter (We checked BATCH_SIZE * 5 addresses)
        counter_queue.put(BATCH_SIZE * 5)

def get_user_patterns():
    print(f"\n{Fore.CYAN}=== VANITY WALLET FINDER (Optimized) ==={Style.RESET_ALL}")
    print("Choose mode:")
    print("1. Quick find (Starts with '1Ace', 'bc1q', '0x777' etc)")
    print("2. Custom pattern")
    print("3. Find addresses with 7+ repeating chars")
    print("4. Lucky mode (777, 888)")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    patterns = {}
    
    if choice == '1':
        patterns['starts_with'] = ["1Ace", "1King", "1Queen", "bc1qcool", "0x000", "0xdead", "0xbad"]
    elif choice == '2':
        p_type = input("Match type (start/end/contains): ").strip().lower()
        val = input("Enter string to find: ").strip()
        if p_type == 'start': patterns['starts_with'] = [val]
        elif p_type == 'end': patterns['ends_with'] = [val]
        elif p_type == 'contains': patterns['contains'] = [val]
    elif choice == '3':
        patterns['repeating'] = 7
        print("\nWhere to match?")
        print("1. Anywhere")
        print("2. At the end")
        sub = input("Choice (1-2): ").strip()
        patterns['repeating_loc'] = 'end' if sub == '2' else 'any'
    elif choice == '4':
        patterns['contains'] = ["777", "888", "999", "000"]
    else:
        print("Invalid choice, defaulting to Quick find.")
        patterns['starts_with'] = ["1Ace", "bc1q", "0xABC"]
        
    return patterns

def get_network():
    print(f"\n{Fore.YELLOW}Select Network:{Style.RESET_ALL}")
    print("1. Bitcoin (Legacy - 1...)")
    print("2. Bitcoin (SegWit - bc1...)")
    print("3. Ethereum (0x...)")
    
    c = input("Choice (1-3): ").strip()
    if c == '1': return 'BTC_LEGACY'
    if c == '2': return 'BTC_SEGWIT'
    if c == '3': return 'ETH'
    return 'ETH'

def main():
    # Setup
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    # User Input
    network = get_network()
    patterns = get_user_patterns()
    
    # CPU Count
    num_processes = max(1, multiprocessing.cpu_count() - 1)
    
    print(f"\n{Fore.GREEN}Starting {num_processes} worker processes...{Style.RESET_ALL}")
    print(f"Network: {network}")
    print(f"Patterns: {patterns}")
    print(f"Checking 5 addresses per mnemonic...")
    
    result_queue = multiprocessing.Queue()
    counter_queue = multiprocessing.Queue()
    
    workers = []
    for _ in range(num_processes):
        p = multiprocessing.Process(target=worker_process, args=(network, patterns, result_queue, counter_queue))
        p.daemon = True
        p.start()
        workers.append(p)
    
    total_checked = 0
    start_time = time.time()
    last_update = start_time
    
    found_wallets = []
    # Current output file handle
    current_file_path = None
    current_file_count = 0
    total_found_session = 0
    
    try:
        while True:
            # Check for results
            try:
                # Get all available results
                while True:
                    result = result_queue.get_nowait()
                    found_wallets.append(result)
                    total_found_session += 1
                    
                    # Print match
                    print(f"\n{Fore.MAGENTA}💎 FOUND MATCH!{Style.RESET_ALL}")
                    print(f"{Fore.WHITE}Address: {result['address']}")
                    print(f"Mnemonic: {result['mnemonic']}")
                    print(f"Index: {result['path_index']}")
                    print(f"Pattern: {result['type']} (Score: {result['score']}/10)")
                    print(f"Found at: {result['timestamp']}{Style.RESET_ALL}\n")
                    
                    # Rotate file if needed
                    if current_file_path is None or current_file_count >= 1000:
                        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                        current_file_path = os.path.join(OUTPUT_DIR, f"addresses_{timestamp_str}.txt")
                        current_file_count = 0
                        print(f"{Fore.BLUE}Creating new output file: {current_file_path}{Style.RESET_ALL}")
                    
                    with open(current_file_path, "a") as f:
                        f.write(f"FOUND: {result['address']}\n")
                        f.write(f"Mnemonic: {result['mnemonic']}\n")
                        f.write(f"Index: {result['path_index']}\n")
                        f.write(f"Score: {result['score']}/10 ({result['type']})\n")
                        f.write(f"Found at: {result['timestamp']}\n")
                        f.write("-" * 50 + "\n")
                    
                    current_file_count += 1
                    
            except Empty:
                pass
            
            # Check counter
            try:
                while True:
                    c = counter_queue.get_nowait()
                    total_checked += c
            except Empty:
                pass
            
            # Update stats
            now = time.time()
            if now - last_update > 0.5:
                elapsed = now - start_time
                if elapsed > 0:
                    speed = total_checked / elapsed
                    sys.stdout.write(f"\r Checked: {total_checked:,} | Speed: {int(speed):,}/sec | Found: {total_found_session} ")
                    sys.stdout.flush()
                    last_update = now
                
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print(f"\n\n{Fore.RED}Stopping...{Style.RESET_ALL}")
        for p in workers:
            p.terminate()
        print(f"Total Checked: {total_checked:,}")
        print(f"Total Found: {total_found_session}")
        print("Goodbye!")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
