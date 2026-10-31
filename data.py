"""Breed knowledge base + helpers.
Tuple: (size, weight, lifespan, energy, grooming, trainability, kids, apartment, temperament) - scores 1-5."""
DB = {
 "golden retriever": ("Large","25-34 kg","10-12 yrs",4,4,5,5,2,"Friendly, intelligent, devoted"),
 "labrador retriever": ("Large","25-36 kg","10-12 yrs",5,2,5,5,2,"Outgoing, eager, gentle"),
 "german shepherd": ("Large","22-40 kg","9-13 yrs",5,3,5,4,2,"Loyal, confident, protective"),
 "beagle": ("Small","9-11 kg","12-15 yrs",4,2,3,5,3,"Curious, merry, scent-driven"),
 "boxer": ("Large","25-32 kg","10-12 yrs",5,1,4,5,2,"Playful, bright, energetic"),
 "pug": ("Small","6-8 kg","12-15 yrs",2,2,3,5,5,"Charming, mischievous, loving"),
 "siberian husky": ("Medium","16-27 kg","12-14 yrs",5,4,2,4,1,"Outgoing, independent, vocal"),
 "pomeranian": ("Toy","1.5-3 kg","12-16 yrs",3,4,3,2,5,"Bold, lively, alert"),
 "chihuahua": ("Toy","1.5-3 kg","14-16 yrs",2,1,3,2,5,"Graceful, charming, sassy"),
 "shih tzu": ("Toy","4-7 kg","10-16 yrs",2,5,3,4,5,"Affectionate, playful, outgoing"),
 "rottweiler": ("Large","35-60 kg","9-10 yrs",4,2,4,3,2,"Loyal, confident, calm guardian"),
 "great dane": ("Giant","45-90 kg","7-10 yrs",3,2,3,4,2,"Friendly, patient, gentle giant"),
 "french bulldog": ("Small","8-14 kg","10-12 yrs",2,1,3,4,5,"Adaptable, playful, smart"),
 "miniature poodle": ("Small","5-9 kg","12-15 yrs",3,5,5,4,5,"Active, proud, very smart"),
 "standard poodle": ("Large","20-32 kg","12-15 yrs",4,5,5,4,3,"Elegant, athletic, eager"),
 "toy poodle": ("Toy","2-4 kg","12-18 yrs",3,5,5,3,5,"Clever, lively, devoted"),
 "border collie": ("Medium","14-20 kg","12-15 yrs",5,3,5,3,1,"Driven, brilliant, intense"),
 "yorkshire terrier": ("Toy","2-3 kg","11-15 yrs",3,5,3,2,5,"Feisty, affectionate, brave"),
 "doberman": ("Large","30-40 kg","10-12 yrs",4,1,5,3,2,"Alert, fearless, loyal"),
 "samoyed": ("Medium","16-30 kg","12-14 yrs",4,5,3,5,2,"Gentle, adaptable, sociable"),
 "saint bernard": ("Giant","55-80 kg","8-10 yrs",2,3,3,5,1,"Calm, patient, charming"),
 "bernese mountain dog": ("Large","32-52 kg","7-10 yrs",3,4,4,5,2,"Good-natured, calm, strong"),
 "pembroke": ("Small","10-14 kg","12-14 yrs",4,3,5,4,3,"Affectionate, smart, outgoing"),
 "maltese dog": ("Toy","2-4 kg","12-15 yrs",2,5,3,3,5,"Gentle, playful, fearless"),
 "cocker spaniel": ("Small","12-15 kg","10-14 yrs",3,4,4,5,4,"Gentle, smart, happy"),
 "shetland sheepdog": ("Small","6-12 kg","12-14 yrs",4,4,5,4,4,"Playful, strong, bright"),
 "vizsla": ("Medium","20-30 kg","12-14 yrs",5,1,4,4,2,"Affectionate, energetic, gentle"),
 "basset": ("Medium","20-29 kg","12-13 yrs",2,2,2,5,3,"Patient, low-key, charming"),
 "whippet": ("Medium","9-18 kg","12-15 yrs",3,1,4,4,4,"Calm, affectionate, sprinter"),
 "boston bull": ("Small","5-11 kg","11-13 yrs",3,1,4,5,5,"Friendly, bright, amusing"),
 "papillon": ("Toy","3-5 kg","13-16 yrs",3,3,5,3,5,"Happy, alert, friendly"),
 "newfoundland": ("Giant","45-70 kg","9-10 yrs",2,4,4,5,1,"Sweet, patient, devoted"),
 "miniature schnauzer": ("Small","5-9 kg","12-15 yrs",3,4,4,4,5,"Friendly, smart, obedient"),
}
DEFAULT = ("Medium","n/a","10-13 yrs",3,3,3,3,3,"Profile not curated yet - see the Wikipedia summary")
FIELDS = ["size","weight","life","energy","grooming","train","kids","apt","temper"]
WIKI = {"boston bull":"Boston Terrier","pembroke":"Pembroke Welsh Corgi","chow":"Chow Chow","malamute":"Alaskan Malamute",
 "eskimo dog":"American Eskimo Dog","basset":"Basset Hound","bull mastiff":"Bullmastiff","doberman":"Dobermann",
 "lhasa":"Lhasa Apso","blenheim spaniel":"Cavalier King Charles Spaniel","english springer":"English Springer Spaniel",
 "mexican hairless":"Xoloitzcuintli","collie":"Rough Collie"}

def pretty(raw):
    return raw.replace("_"," ").replace("-"," ").title() if raw.islower() else raw.replace("_"," ")

def norm(raw):
    return raw.replace("_"," ").lower()

def profile(raw):
    k = norm(raw)
    p = dict(zip(FIELDS, DB.get(k, DEFAULT)))
    p["curated"] = k in DB
    return p