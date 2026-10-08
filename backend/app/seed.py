"""Idempotent reference data: schemes and languages."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import GovernmentScheme, Language

SCHEMES = [
    dict(code="PM-KISAN", name="Pradhan Mantri Kisan Samman Nidhi", category="income", state="All India",
         benefit="Rs 6,000 per year paid directly to the bank account in three instalments of Rs 2,000.",
         eligibility="Land holding farmer families. Institutional land holders, income tax payers and pensioners above Rs 10,000/month are excluded.",
         documents=["Aadhaar", "Land record (pattadar passbook)", "Bank passbook"],
         how_to_apply="Register at the village revenue office or self-register on the PM-KISAN portal, then complete eKYC.",
         link="https://pmkisan.gov.in"),
    dict(code="PMFBY", name="Pradhan Mantri Fasal Bima Yojana (crop insurance)", category="insurance", state="All India",
         benefit="Insurance against yield loss from drought, flood, pest and post-harvest damage. Farmer pays 2% of sum insured for kharif, 1.5% for rabi and 5% for commercial crops.",
         eligibility="All farmers growing notified crops in notified areas, including tenant and share croppers.",
         documents=["Aadhaar", "Land record or tenancy agreement", "Bank passbook", "Sowing certificate"],
         how_to_apply="Apply through the bank where the crop loan is taken, a common service centre, or the PMFBY portal before the season cut-off date.",
         link="https://pmfby.gov.in"),
    dict(code="KCC", name="Kisan Credit Card", category="credit", state="All India",
         benefit="Crop loan up to Rs 3 lakh at 7% interest, reduced to 4% with prompt repayment. Also covers dairy, fishery and allied activities.",
         eligibility="All farmers, tenant farmers, oral lessees and share croppers.",
         documents=["Aadhaar", "Land record", "Passport photo", "Bank account"],
         how_to_apply="Apply at any commercial bank, regional rural bank or cooperative bank branch, or through the Jan Samarth portal.",
         link="https://www.myscheme.gov.in/schemes/kcc"),
    dict(code="SHC", name="Soil Health Card Scheme", category="soil", state="All India",
         benefit="Free soil testing every two years with a crop-wise nutrient recommendation card.",
         eligibility="All farmers.",
         documents=["Aadhaar", "Land record"],
         how_to_apply="Give a soil sample at the village agriculture office or the nearest soil testing laboratory.",
         link="https://soilhealth.dac.gov.in"),
    dict(code="PMKSY", name="Pradhan Mantri Krishi Sinchayee Yojana (micro irrigation)", category="irrigation", state="All India",
         benefit="Subsidy of 55% for small and marginal farmers and 45% for others on drip and sprinkler systems.",
         eligibility="Farmers with an assured water source and clear land title.",
         documents=["Aadhaar", "Land record", "Water source certificate", "Bank passbook"],
         how_to_apply="Apply through the district horticulture or agriculture office with a quotation from an empanelled supplier.",
         link="https://pmksy.gov.in"),
    dict(code="PM-KUSUM", name="PM-KUSUM solar pump scheme", category="energy", state="All India",
         benefit="Up to 60% subsidy on standalone solar agriculture pumps and support for solarising existing grid pumps.",
         eligibility="Individual farmers, cooperatives, panchayats and farmer producer organisations.",
         documents=["Aadhaar", "Land record", "Bank passbook", "Electricity connection details"],
         how_to_apply="Apply on the state renewable energy development agency portal when the annual window opens.",
         link="https://pmkusum.mnre.gov.in"),
    dict(code="ENAM", name="eNAM national agriculture market", category="market", state="All India",
         benefit="Online bidding across mandis so produce reaches more buyers, with transparent price discovery and online payment.",
         eligibility="Any farmer selling at a linked APMC mandi.",
         documents=["Aadhaar", "Bank passbook", "Mobile number"],
         how_to_apply="Register at the nearest eNAM linked mandi or on the eNAM portal or app.",
         link="https://enam.gov.in"),
    dict(code="RYTHU-BHAROSA", name="Rythu Bharosa (Telangana investment support)", category="income", state="Telangana",
         benefit="Per-acre investment support paid before each cropping season to help meet input costs.",
         eligibility="Land owning farmers in Telangana with an updated pattadar passbook.",
         documents=["Pattadar passbook", "Aadhaar", "Bank account"],
         how_to_apply="Verify land records with the mandal revenue office; payment is credited automatically to the linked account.",
         link="https://rythubandhu.telangana.gov.in"),
    dict(code="AIF", name="Agriculture Infrastructure Fund", category="credit", state="All India",
         benefit="Loans up to Rs 2 crore with a 3% interest subvention for warehouses, cold storage, grading units and primary processing.",
         eligibility="Farmers, FPOs, self help groups, cooperatives, agri-entrepreneurs and startups.",
         documents=["Project report", "Land documents", "KYC", "Bank account"],
         how_to_apply="Apply on the Agri Infra Fund portal; the lending bank sanctions the loan.",
         link="https://agriinfra.dac.gov.in"),
    dict(code="NMNF", name="National Mission on Natural Farming", category="soil", state="All India",
         benefit="Assistance for input preparation units, cluster formation and training for chemical-free farming.",
         eligibility="Farmers willing to adopt natural farming in a cluster of 50 hectares.",
         documents=["Aadhaar", "Land record", "Cluster membership proof"],
         how_to_apply="Enrol through the district agriculture office or the Krishi Vigyan Kendra running the cluster.",
         link="https://naturalfarming.dac.gov.in"),
]

LANGUAGES = [
    ("en", "English", "English"),
    ("hi", "Hindi", "हिन्दी"),
    ("te", "Telugu", "తెలుగు"),
    ("ta", "Tamil", "தமிழ்"),
    ("kn", "Kannada", "ಕನ್ನಡ"),
    ("mr", "Marathi", "मराठी"),
    ("bn", "Bengali", "বাংলা"),
    ("pa", "Punjabi", "ਪੰਜਾਬੀ"),
]


async def seed(db: AsyncSession) -> None:
    existing = set((await db.execute(select(GovernmentScheme.code))).scalars().all())
    for s in SCHEMES:
        if s["code"] not in existing:
            db.add(GovernmentScheme(**s))
    have = set((await db.execute(select(Language.code))).scalars().all())
    for code, label, native in LANGUAGES:
        if code not in have:
            db.add(Language(code=code, label=label, native=native))
    await db.commit()
