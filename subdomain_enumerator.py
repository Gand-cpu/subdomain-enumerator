import dns.resolver
import argparse
import concurrent.futures
import os
from tqdm import tqdm

resolver = dns.resolver.Resolver()
resolver.timeout = 2
resolver.lifetime = 2

found_subdomains = []

def resolve_subdomain(domain, subdomain):
    full_domain = f"{subdomain}.{domain}"
    try:
        answers = resolver.resolve(full_domain, 'A')
        return full_domain
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.LifetimeTimeout, dns.resolver.NoNameservers):
        return None

def load_wordlist(wordlist_path):
    if not os.path.exists(wordlist_path):
        raise FileNotFoundError(f"Wordlist not found: {wordlist_path}")
    with open(wordlist_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def wildcard_check(domain, test_sub="wildcard-check"):
    try:
        test_domain = f"{test_sub}.{domain}"
        resolver.resolve(test_domain, 'A')
        return True
    except:
        return False

def main(domain, wordlist_path, threads, output_file):
    subdomains = load_wordlist(wordlist_path)
    use_wildcard = wildcard_check(domain)

    print(f"\n[*] Wildcard DNS Detected: {'Yes' if use_wildcard else 'No'}\n")
    print(f"[*] Enumerating subdomains for: {domain}\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(resolve_subdomain, domain, sub): sub for sub in subdomains}
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(subdomains), desc="Progress"):
            result = future.result()
            if result:
                found_subdomains.append(result)
                print(f"[+] Found: {result}")

    if output_file:
        with open(output_file, 'w') as f:
            for sub in found_subdomains:
                f.write(sub + '\n')
        print(f"\n[+] Results saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Advanced Subdomain Enumerator using DNS")
    parser.add_argument("domain", help="Target domain (e.g. example.com)")
    parser.add_argument("-w", "--wordlist", help="Path to wordlist", required=True)
    parser.add_argument("-t", "--threads", help="Number of threads (default=20)", type=int, default=20)
    parser.add_argument("-o", "--output", help="File to save results", default=None)
    args = parser.parse_args()

    try:
        main(args.domain, args.wordlist, args.threads, args.output)
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user. Exiting...")
