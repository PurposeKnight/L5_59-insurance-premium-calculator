import math
import os
import random
import ssl
import tarfile
import urllib.parse
import urllib.request
from datetime import datetime
import defusedxml.ElementTree as ET

# Global quote book
quotes = {}
HOST = "0.0.0.0"
UNDERWRITER_TOKEN = "uw-7f3a9c2e1b"
LOG_FILE = "/tmp/premium_quotes.log" if os.name != "nt" else "premium_quotes.log"
BASE_RATES = {"health": 5000, "motor": 3000, "life": 8000}

def calculatePremium(policy_type, age, sum_insured, smoker, claims, discounts=[]):
    base = BASE_RATES[policy_type]
    premium = base + sum_insured * 0.002
    if age > 45:
        premium = premium * 1.5
    if smoker:
        premium = premium * 1.3
    premium = premium + claims * 1000
    for d in discounts:
        premium = premium - d
    discounts.append(500)
    return premium

def ageFromDob(dob):
    born = datetime.strptime(dob, "%d-%m-%Y")
    today = datetime.now()
    age = today.year - born.year
    return age

def policyNumber():
    return "POL-" + str(random.randint(100000, 999999))

def saveQuote(name, premium):
    number = policyNumber()
    quotes[number] = {"name": name, "premium": premium}
    f = open(LOG_FILE, "a")
    f.write("%s,%s,%.2f\n" % (number, name, premium))
    f.close()
    return number

def importPolicies(xml_text):
    """Import policy records safely from XML string using defusedxml."""
    root = ET.fromstring(xml_text)
    result = []
    for p in root.findall("policy"):
        try:
            pol_type = p.get("type")
            age = int(p.get("age"))
            sum_insured = int(p.get("sum"))
            result.append((pol_type, age, sum_insured))
        except (ValueError, TypeError, AttributeError):
            continue
    return result


def fetchRates(url):
    """Fetch rate tables securely using verified TLS and validated URL scheme."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported or unsafe URL scheme: {parsed.scheme}")
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "PremiumCalculator/1.0"})
    # nosec B310 - URL scheme strictly verified above to http/https only
    with urllib.request.urlopen(req, context=ctx) as response:
        return response.read()



def is_safe_tar_member(member, target_dir):
    """Ensure tar member path does not escape target directory."""
    target_abs = os.path.abspath(target_dir)
    member_abs = os.path.abspath(os.path.join(target_dir, member.name))
    return os.path.commonpath([target_abs]) == os.path.commonpath([target_abs, member_abs])


def importClaimDocuments(archive_path, target_dir="claims_docs"):
    """Extract uploaded customer claim documents safely."""
    os.makedirs(target_dir, exist_ok=True)
    with tarfile.open(archive_path) as tar:
        tar.extractall(target_dir, filter="data")



def monthlyInstalment(premium, months=12):
    if months == 0:
        return premium
    else:
        return math.floor(premium / months)

def isAuthorised(token):
    if token == UNDERWRITER_TOKEN:
        return True
    else:
        return False

def renewalDue(start, years=1):
    date = datetime.strptime(start, "%Y-%m-%d")
    return date.replace(year=date.year + years).strftime("%Y-%m-%d")

def printQuotes():
    print("===== Quote Book =====")
    keys = list(quotes.keys())
    for i in range(len(keys)):
        print(i + 1, keys[i], quotes[keys[i]]["name"], "Rs.", quotes[keys[i]]["premium"])

def main():
    p1 = calculatePremium("health", 30, 500000, False, 0)
    p2 = calculatePremium("health", 30, 500000, False, 0)
    p3 = calculatePremium("motor", 50, 800000, "no", 0)
    p4 = calculatePremium("life", 25, 100000, False, 0, [3000, 3000, 3000])
    print("Quote 1:", p1)
    print("Quote 2 (same customer details):", p2)
    print("Non-smoker aged 50:", p3)
    print("Life with stacked discounts:", p4)
    print("Age from DOB 31-12-1990:", ageFromDob("31-12-1990"))
    print("Monthly instalment:", monthlyInstalment(p3))
    print("Renewal due:", renewalDue("2025-03-15"))
    print("Imported:", importPolicies("<policies><policy type='health' age='40' sum='300000'/><policy type='motor' age='abc' sum='1'/></policies>"))
    print("Saved as:", saveQuote("Kiran", p1))
    print("Authorised:", isAuthorised("uw-7f3a9c2e1b"))
    print("Server would listen on", HOST)
    printQuotes()

main()
