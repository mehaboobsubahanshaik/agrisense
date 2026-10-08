"""Curated agricultural knowledge base.

These documents are the retrieval corpus for the RAG pipeline. They are indexed
into ChromaDB on startup (when reachable) and also into an in-process TF-IDF
index so that retrieval keeps working with no network and no vector database.

Sources of the agronomic figures: ICAR package-of-practices, state agriculture
department advisories and Krishi Vigyan Kendra bulletins (India).
"""

DOCS: list[dict] = [
    {
        "id": "cost-of-cultivation",
        "title": "Cost of cultivation by crop (indicative, per acre)",
        "crop": "all",
        "text": (
            "Which crops cost the most to grow, and which are the cheapest. "
            "Indicative variable cost of cultivation per acre in India, covering seed, fertiliser, "
            "plant protection, labour and machine hire, and excluding land rent. Highest cost crops: "
            "banana about 120000 to 180000 rupees per acre, turmeric 90000 to 130000, chilli 80000 to "
            "120000, tomato 60000 to 90000, onion 50000 to 70000, sugarcane plant crop 55000 to 70000. "
            "Medium cost crops: Bt cotton 35000 to 45000, paddy 30000 to 40000, groundnut 28000 to 35000, "
            "wheat 22000 to 28000, maize 20000 to 26000. Lowest cost crops are the pulses: pigeonpea "
            "18000 to 25000, soybean 18000 to 24000, chickpea 15000 to 20000, greengram 12000 to 18000. "
            "High cost crops also carry high price risk, because a market crash after spending 1 lakh per "
            "acre on chilli or turmeric hurts far more than a crash in chickpea. Costs vary by district, "
            "season and labour rate, so confirm current local figures with your Krishi Vigyan Kendra or "
            "the district agriculture office before planning."
        ),
    },
    {
        "id": "crop-economics",
        "title": "Comparing crop profitability and price risk",
        "crop": "all",
        "text": (
            "To compare two crops, work out net return per acre, not yield. Net return equals expected "
            "yield in quintals per acre multiplied by expected price per quintal, minus the cost of "
            "cultivation. Pulses and oilseeds have low cost and moderate return, and they fix nitrogen "
            "which cuts the fertiliser bill of the next crop. Vegetables and spices have the highest "
            "gross return per acre but also the highest cost, the highest labour requirement and the "
            "most volatile prices. Paddy and wheat have assured procurement at minimum support price in "
            "many states, which lowers price risk even though margins are thin. Do not put the whole "
            "holding into one high value crop: split the area so that a price crash in one crop does not "
            "take the season with it. Minimum support prices are announced every year before the season "
            "by the Government of India, so always check the current year rate rather than last year's."
        ),
    },
    {
        "id": "market-price-sources",
        "title": "Where to check crop prices and mandi rates",
        "crop": "all",
        "text": (
            "Daily mandi arrival and price data for every regulated market in India is published on the "
            "Agmarknet portal run by the Directorate of Marketing and Inspection. The eNAM platform "
            "shows live bids across linked mandis and lets a farmer sell outside the local market. State "
            "agriculture department portals and the Kisan Call Centre on 1800-180-1551 also give current "
            "rates. For an assured floor price, check the minimum support price for the current season "
            "and whether your state has opened procurement centres for that crop. Compare at least two "
            "nearby mandis before transporting produce, because the price difference often exceeds the "
            "transport cost."
        ),
    },
    {
        "id": "input-cost-saving",
        "title": "Reducing the cost of cultivation",
        "crop": "all",
        "text": (
            "The largest controllable costs are fertiliser, plant protection and labour. Soil testing "
            "before every season typically cuts the fertiliser bill by 15 to 25 percent, because most "
            "farmers over-apply nitrogen and under-apply potash. Applying urea in splits guided by a leaf "
            "colour chart avoids wasted top dressing. Seed treatment costing a few rupees per kilogram "
            "prevents early disease that would otherwise need repeated sprays. Growing a legume in "
            "rotation adds 20 to 40 kg of nitrogen per hectare for the following crop. Farm machinery "
            "hire through a custom hiring centre is cheaper than owning equipment for a small holding. "
            "Drip irrigation cuts both water and labour, and is subsidised under the per drop more crop "
            "component of PMKSY."
        ),
    },
    {
        "id": "rice-nutrition",
        "title": "Rice (paddy) nutrient management",
        "crop": "rice",
        "text": (
            "Recommended dose of fertiliser for transplanted paddy in India is about 120 kg N, "
            "60 kg P2O5 and 40 kg K2O per hectare for medium duration varieties. Apply nitrogen in "
            "three splits: 50 percent basal, 25 percent at active tillering (20-25 days after "
            "transplanting) and 25 percent at panicle initiation. Full phosphorus goes as basal. "
            "Potash is split half basal and half at panicle initiation. Use a leaf colour chart to "
            "avoid over-application of urea. Zinc sulphate 25 kg per hectare corrects the zinc "
            "deficiency common in continuously flooded soils."
        ),
    },
    {
        "id": "rice-water",
        "title": "Rice irrigation and water saving",
        "crop": "rice",
        "text": (
            "Paddy needs roughly 1200 to 1500 mm of water per season. Alternate wetting and drying "
            "saves 25 to 30 percent water without yield loss: let the field dry until the water "
            "level falls 15 cm below the surface, then re-flood to 5 cm. Keep 2-5 cm standing water "
            "from panicle initiation to flowering, the most drought sensitive stage. Drain the field "
            "10 days before harvest."
        ),
    },
    {
        "id": "rice-blast",
        "title": "Rice blast disease",
        "crop": "rice",
        "text": (
            "Rice blast is caused by Magnaporthe oryzae. Symptoms are spindle shaped lesions with "
            "grey centres and brown margins on leaves, and blackening at the panicle neck. It is "
            "favoured by night temperature of 20-25 C, leaf wetness above 10 hours and heavy "
            "nitrogen. Manage with resistant varieties, balanced nitrogen in splits, and a spray of "
            "tricyclazole 75 WP at 0.6 g per litre or isoprothiolane 40 EC at 1.5 ml per litre at "
            "first symptom, repeated after 12-15 days. Seed treatment with carbendazim 2 g per kg "
            "reduces primary infection."
        ),
    },
    {
        "id": "rice-bph",
        "title": "Brown plant hopper in rice",
        "crop": "rice",
        "text": (
            "Brown plant hopper causes hopper burn: circular patches of drying plants. Insects sit "
            "at the base of the plant above the water line. Economic threshold is 10 hoppers per "
            "hill. Avoid excess nitrogen and close spacing, drain the field for 3-4 days, and spray "
            "pymetrozine 50 WG at 0.6 g per litre or dinotefuran 20 SG at 0.3 g per litre directed "
            "at the base of the plant. Conserve mirid bugs and spiders, which are natural enemies."
        ),
    },
    {
        "id": "cotton-bollworm",
        "title": "Pink bollworm in cotton",
        "crop": "cotton",
        "text": (
            "Pink bollworm larvae bore into flowers and bolls, producing rosette flowers and stained "
            "lint. Install pheromone traps at 5 per acre from 45 days after sowing and monitor: 8 "
            "moths per trap per night for three nights is the action threshold. Remove and destroy "
            "rosette flowers, avoid extending the crop beyond December, and spray profenophos 50 EC "
            "at 2 ml per litre or emamectin benzoate 5 SG at 0.4 g per litre. Follow a strict "
            "refuge-in-bag planting to slow resistance."
        ),
    },
    {
        "id": "cotton-nutrition",
        "title": "Cotton nutrient and spacing practice",
        "crop": "cotton",
        "text": (
            "Bt cotton in black soil needs about 120 kg N, 60 kg P2O5 and 60 kg K2O per hectare. "
            "Nitrogen is applied in four splits from 30 to 90 days after sowing. Spacing of 90 by 60 "
            "cm suits irrigated conditions. Magnesium and boron deficiency is common: spray 0.5 "
            "percent magnesium sulphate and 0.2 percent boron at square formation to reduce square "
            "and boll shedding."
        ),
    },
    {
        "id": "tomato-blight",
        "title": "Early and late blight of tomato",
        "crop": "tomato",
        "text": (
            "Early blight (Alternaria solani) gives brown concentric ring spots on older leaves. "
            "Late blight (Phytophthora infestans) gives water soaked greasy patches with white "
            "downy growth on the underside, spreading fast in cool humid weather below 20 C. Spray "
            "mancozeb 75 WP at 2.5 g per litre preventively; for late blight use cymoxanil plus "
            "mancozeb at 3 g per litre or metalaxyl plus mancozeb. Stake plants, avoid overhead "
            "irrigation in the evening, and rotate away from solanaceous crops for two seasons."
        ),
    },
    {
        "id": "maize-fall-armyworm",
        "title": "Fall armyworm in maize",
        "crop": "maize",
        "text": (
            "Fall armyworm larvae feed inside the whorl and leave ragged holes and moist sawdust "
            "like frass. Scout 20 plants at five spots; treat when 5 to 10 percent of whorls are "
            "damaged. Apply sand plus lime mixture in the whorl for early instars, use pheromone "
            "traps at 5 per acre, release Trichogramma cards, and spray emamectin benzoate 5 SG at "
            "0.4 g per litre or spinetoram 11.7 SC at 0.5 ml per litre directed into the whorl in "
            "the evening."
        ),
    },
    {
        "id": "wheat-rust",
        "title": "Yellow and brown rust of wheat",
        "crop": "wheat",
        "text": (
            "Yellow rust appears as yellow-orange pustules in stripes between leaf veins in cool "
            "weather; brown rust makes scattered orange-brown pustules. Sow resistant varieties, "
            "avoid late sowing and excess nitrogen, and spray propiconazole 25 EC at 1 ml per litre "
            "at first pustule, repeating after 15 days if the weather stays cool and humid."
        ),
    },
    {
        "id": "soil-ph",
        "title": "Soil pH correction",
        "crop": "general",
        "text": (
            "Most field crops perform best between pH 6.0 and 7.5. Acidic soil below 5.5 locks up "
            "phosphorus and releases toxic aluminium: apply 2 to 4 quintals of agricultural lime per "
            "acre before the monsoon and re-test after one season. Alkaline soil above 8.2 with high "
            "sodium needs gypsum at 2 to 5 quintals per acre plus green manuring with dhaincha and "
            "good drainage. Never apply lime and phosphatic fertiliser together."
        ),
    },
    {
        "id": "soil-organic",
        "title": "Organic carbon and organic farming",
        "crop": "general",
        "text": (
            "Organic carbon below 0.5 percent is low, 0.5 to 0.75 is medium and above 0.75 is high. "
            "Raise it with 5 tonnes of farmyard manure per acre, green manuring with sunhemp or "
            "dhaincha ploughed in at 45 days, vermicompost at 2 tonnes per acre, and crop residue "
            "retention. Jeevamrutham, panchagavya at 3 percent spray, and neem cake at 100 kg per "
            "acre are standard low-cost organic inputs. Biofertilisers: Azospirillum or Rhizobium "
            "plus phosphate solubilising bacteria at 5 kg per acre reduce chemical nitrogen and "
            "phosphorus needs by roughly a quarter."
        ),
    },
    {
        "id": "npk-interpretation",
        "title": "Reading a soil health card",
        "crop": "general",
        "text": (
            "Available nitrogen is low below 280 kg per hectare, medium from 280 to 560 and high "
            "above 560. Available phosphorus (P2O5) is low below 10, medium 10 to 25 and high above "
            "25. Available potassium (K2O) is low below 120, medium 120 to 280 and high above 280. "
            "For a low rating add 25 percent above the recommended dose, for high subtract 25 "
            "percent. Urea contains 46 percent N, DAP 18 percent N and 46 percent P2O5, single "
            "super phosphate 16 percent P2O5, and muriate of potash 60 percent K2O."
        ),
    },
    {
        "id": "irrigation-schedule",
        "title": "Irrigation scheduling and critical stages",
        "crop": "general",
        "text": (
            "Irrigate at the critical stages rather than on a fixed calendar. Rice: tillering, "
            "panicle initiation and flowering. Wheat: crown root initiation at 21 days, tillering, "
            "flowering and grain filling. Maize: knee high, tasselling and grain filling. Cotton: "
            "squaring, flowering and boll development. Groundnut: pegging and pod development. Drip "
            "irrigation saves 40 to 60 percent water and works with fertigation; mulching cuts "
            "evaporation by around 25 percent. Do not irrigate when 20 mm or more rain is forecast "
            "in the next 48 hours."
        ),
    },
    {
        "id": "crop-rotation",
        "title": "Crop rotation and intercropping",
        "crop": "general",
        "text": (
            "Follow a cereal with a legume to fix nitrogen and break pest cycles: rice-greengram, "
            "cotton-chickpea, maize-soybean. Do not repeat the same family in consecutive seasons, "
            "since soil borne wilts and nematodes build up. Useful intercrops are cotton with "
            "greengram, maize with cowpea and pigeonpea with groundnut in a 1:7 row ratio. A legume "
            "in rotation adds roughly 20 to 40 kg of nitrogen per hectare for the next crop."
        ),
    },
    {
        "id": "weather-advisory",
        "title": "Weather based field decisions",
        "crop": "general",
        "text": (
            "Do not spray when rain is expected within 6 hours or when wind is above 10 km per hour; "
            "early morning and late evening are the best spray windows. Sow only after 25 to 30 mm "
            "of cumulative rain has wetted the profile, to avoid a failed germination. Frost warning "
            "below 4 C: irrigate the field in the evening and light smoke on the windward side. "
            "Heatwave above 40 C at flowering: give a light irrigation and spray 2 percent potassium "
            "nitrate. Drought: switch to short duration varieties, use mulch and spray 2 percent "
            "urea or kaolin as an anti-transpirant."
        ),
    },
    {
        "id": "schemes-overview",
        "title": "Central government support for farmers",
        "crop": "general",
        "text": (
            "PM-KISAN pays 6000 rupees a year in three instalments to land holding farmer families. "
            "Pradhan Mantri Fasal Bima Yojana insures notified crops with a farmer premium of 2 "
            "percent for kharif, 1.5 percent for rabi and 5 percent for commercial crops; enrol "
            "before the cut-off date for the season. The Kisan Credit Card gives crop loans up to 3 "
            "lakh rupees at 7 percent with a 3 percent prompt repayment incentive. The Soil Health "
            "Card scheme gives a free soil test every two years. PM-KUSUM subsidises solar pumps. "
            "eNAM is the online national market for produce. Applications are made at the local "
            "agriculture office, the common service centre, or on the scheme portal with Aadhaar, "
            "land records and a bank passbook."
        ),
    },
    {
        "id": "seed-treatment",
        "title": "Seed treatment and nursery hygiene",
        "crop": "general",
        "text": (
            "Treat seed before sowing to prevent early disease: carbendazim or thiram at 2 g per kg "
            "for fungal seed and soil borne disease, imidacloprid at 5 ml per kg against sucking "
            "pests, and Trichoderma viride at 5 to 10 g per kg as a biological option. Treat with "
            "fungicide first, then insecticide, then biofertiliser, and dry in the shade. Raise "
            "nursery beds 15 cm above ground, solarise with clear plastic for 3 weeks in summer, and "
            "never take a nursery from a field that had wilt last season."
        ),
    },
    {
        "id": "post-harvest",
        "title": "Post harvest handling and marketing",
        "crop": "general",
        "text": (
            "Harvest grain at 20 to 22 percent moisture and dry to 12 to 14 percent before storage, "
            "since above 14 percent storage fungi and aflatoxin develop. Store in clean, dry, "
            "ventilated rooms on wooden pallets, and use neem leaves or approved fumigation against "
            "storage insects. Grade produce before sale; graded lots typically fetch 5 to 15 percent "
            "more. Check the minimum support price and the local mandi rate on eNAM before selling, "
            "and consider a warehouse receipt loan instead of a distress sale at harvest."
        ),
    },
]

# Remedy database keyed by the disease classes the vision model can return.
DISEASE_LIBRARY: dict[str, dict] = {
    "rice_blast": {
        "label": "Rice blast",
        "crop": "rice",
        "symptoms": "Spindle shaped grey-centred lesions on leaves; neck of the panicle turns black.",
        "chemical": ["Tricyclazole 75 WP - 0.6 g/litre", "Isoprothiolane 40 EC - 1.5 ml/litre"],
        "organic": ["Pseudomonas fluorescens 0.2% spray", "Neem oil 3 ml/litre", "Cow urine 10% spray"],
        "cultural": [
            "Split nitrogen; stop top dressing until the spread stops",
            "Drain the field for 2-3 days to reduce leaf wetness",
            "Destroy infected stubble after harvest",
        ],
    },
    "bacterial_leaf_blight": {
        "label": "Bacterial leaf blight",
        "crop": "rice",
        "symptoms": "Yellow wavy margins drying from the leaf tip downwards; milky ooze in the morning.",
        "chemical": ["Copper oxychloride 50 WP 2.5 g/litre + streptocycline 0.15 g/litre"],
        "organic": ["Pseudomonas fluorescens 10 g/litre", "Reduce standing water"],
        "cultural": ["Avoid excess nitrogen", "Drain the field", "Use resistant varieties next season"],
    },
    "leaf_spot": {
        "label": "Leaf spot complex (Cercospora / Alternaria)",
        "crop": "general",
        "symptoms": "Round to angular brown spots, often with a yellow halo, starting on older leaves.",
        "chemical": ["Mancozeb 75 WP - 2.5 g/litre", "Propiconazole 25 EC - 1 ml/litre"],
        "organic": ["Trichoderma viride soil application", "Neem oil 5 ml/litre weekly"],
        "cultural": ["Remove and burn affected lower leaves", "Avoid overhead irrigation", "Widen spacing for airflow"],
    },
    "leaf_rust": {
        "label": "Rust",
        "crop": "wheat",
        "symptoms": "Orange to brown powdery pustules that rub off on the finger.",
        "chemical": ["Propiconazole 25 EC - 1 ml/litre", "Tebuconazole 25.9 EC - 1 ml/litre"],
        "organic": ["Sulphur 80 WP 2 g/litre at early stage"],
        "cultural": ["Avoid late sowing", "Balanced nitrogen", "Resistant variety next season"],
    },
    "powdery_mildew": {
        "label": "Powdery mildew",
        "crop": "general",
        "symptoms": "White powdery patches on the upper leaf surface, leaves curl and dry.",
        "chemical": ["Wettable sulphur 80 WP - 2 g/litre", "Hexaconazole 5 EC - 1 ml/litre"],
        "organic": ["Milk spray 1:9 with water", "Potassium bicarbonate 5 g/litre"],
        "cultural": ["Improve air movement", "Avoid water stress", "Remove infected shoots"],
    },
    "late_blight": {
        "label": "Late blight",
        "crop": "tomato",
        "symptoms": "Greasy dark water soaked patches with white growth underneath; spreads within days.",
        "chemical": ["Cymoxanil 8% + mancozeb 64% - 3 g/litre", "Metalaxyl + mancozeb - 2.5 g/litre"],
        "organic": ["Bordeaux mixture 1%", "Copper hydroxide"],
        "cultural": ["Stake plants", "Remove infected plants immediately", "Do not irrigate in the evening"],
    },
    "early_blight": {
        "label": "Early blight",
        "crop": "tomato",
        "symptoms": "Brown spots with concentric rings on older leaves, leaf drop from the bottom up.",
        "chemical": ["Mancozeb 75 WP - 2.5 g/litre", "Azoxystrobin 23 SC - 1 ml/litre"],
        "organic": ["Neem oil 5 ml/litre", "Trichoderma drench"],
        "cultural": ["Mulch to stop soil splash", "Rotate out of solanaceous crops", "Remove lower leaves"],
    },
    "pest_damage": {
        "label": "Insect pest damage",
        "crop": "general",
        "symptoms": "Chewed margins, holes, whorl damage or sticky honeydew with sooty mould.",
        "chemical": ["Emamectin benzoate 5 SG - 0.4 g/litre", "Chlorantraniliprole 18.5 SC - 0.3 ml/litre"],
        "organic": ["Neem seed kernel extract 5%", "Bt (Bacillus thuringiensis) 1 g/litre", "Pheromone traps 5/acre"],
        "cultural": ["Install bird perches", "Hand pick larvae in the evening", "Destroy egg masses"],
    },
    "nutrient_deficiency": {
        "label": "Nutrient deficiency",
        "crop": "general",
        "symptoms": "Uniform yellowing (nitrogen), interveinal yellowing (magnesium/iron) or scorched margins (potassium).",
        "chemical": ["Urea 2% foliar spray", "Zinc sulphate 0.5% + lime", "Magnesium sulphate 0.5%"],
        "organic": ["Vermicompost 2 t/acre", "Jeevamrutham drench", "Panchagavya 3% spray"],
        "cultural": ["Get a soil test before the next dose", "Correct pH first, it controls availability"],
    },
    "healthy": {
        "label": "Healthy crop",
        "crop": "general",
        "symptoms": "No disease symptoms found in the image.",
        "chemical": [],
        "organic": ["Continue preventive neem spray every 15 days"],
        "cultural": ["Keep scouting twice a week", "Maintain the current nutrient schedule"],
    },
}
