import multiprocessing
import time
import re
from datetime import datetime
from queue import Empty, Full
from bip_utils import (
    Bip39MnemonicGenerator, Bip39SeedGenerator,
    Bip44, Bip44Coins, Bip44Changes,
    Bip84, Bip84Coins,
    Bip39WordsNum
)

# Constants
BATCH_SIZE = 50

def check_criteria(address, patterns):
    """
    Check if address matches any of the patterns.
    patterns: dict of criteria
    Returns: match_type (str) or None, score (int)
    """
    # Starts with
    if 'starts_with' in patterns and patterns['starts_with']:
        for p in patterns['starts_with']:
            if address.startswith(p):
                return f"Starts with '{p}'", 10

    # Ends with
    if 'ends_with' in patterns and patterns['ends_with']:
        for p in patterns['ends_with']:
            if address.endswith(p):
                return f"Ends with '{p}'", 10

    # Contains
    if 'contains' in patterns and patterns['contains']:
        for p in patterns['contains']:
            if p in address:
                return f"Contains '{p}'", 8

    # Repeating characters
    if 'repeating' in patterns and patterns['repeating']:
        min_repeats = int(patterns['repeating'])
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

def worker_process(network, patterns, result_queue, counter_queue, stop_event):
    """
    Worker process to generate wallets and check patterns.
    """
    try:
        mnemonic_gen = Bip39MnemonicGenerator()
        seed_gen = Bip39SeedGenerator
        
        while not stop_event.is_set():
            # Generate batch
            for _ in range(BATCH_SIZE):
                if stop_event.is_set():
                    return

                # Generate Mnemonic
                mnemonic_phrase = mnemonic_gen.FromWordsNumber(Bip39WordsNum.WORDS_NUM_12)
                seed_bytes = seed_gen(mnemonic_phrase).Generate()
                
                bip_obj_ctx = None
                
                if network == 'ETH':
                    bip_obj_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
                elif network == 'BTC_LEGACY':
                    bip_obj_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
                elif network == 'BTC_SEGWIT':
                    bip_obj_ctx = Bip84.FromSeed(seed_bytes, Bip84Coins.BITCOIN)
                
                # Derive account level
                if network == 'ETH':
                    acc = bip_obj_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
                elif network == 'BTC_LEGACY':
                    acc = bip_obj_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
                elif network == 'BTC_SEGWIT':
                    acc = bip_obj_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
                
                # Scan 5 addresses
                for i in range(5):
                    addr_ctx = acc.AddressIndex(i)
                    address = addr_ctx.PublicKey().ToAddress()
                    
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
            
            # Update counter
            try:
                counter_queue.put(BATCH_SIZE * 5)
            except Full:
                pass
                
    except Exception as e:
        # In case of silent errors in processes
        pass

class GeneratorManager:
    def __init__(self):
        self.processes = []
        self.result_queue = multiprocessing.Queue()
        self.counter_queue = multiprocessing.Queue()
        self.stop_event = multiprocessing.Event()
        
    def start_generation(self, network, patterns, num_processes):
        self.stop_generation() # Ensure stopped first
        self.stop_event.clear()
        
        for _ in range(num_processes):
            p = multiprocessing.Process(
                target=worker_process, 
                args=(network, patterns, self.result_queue, self.counter_queue, self.stop_event)
            )
            p.daemon = True
            p.start()
            self.processes.append(p)
            
    def stop_generation(self):
        self.stop_event.set()
        for p in self.processes:
            p.terminate()
            p.join(timeout=1.0)
        self.processes = []
        
        # Clear queues
        while not self.result_queue.empty():
            try: self.result_queue.get_nowait()
            except Empty: break
        while not self.counter_queue.empty():
            try: self.counter_queue.get_nowait()
            except Empty: break
