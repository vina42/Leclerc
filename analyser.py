import os, re
from datetime import datetime, timezone
from urllib.parse import urljoin
import requests, fitz, pandas as pd
from bs4 import BeautifulSoup

CATALOG_URL = "https://www.e.leclerc/prospectus"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CataloguePromoResearch/1.0)"}
MAX_PDFS = 30
PROMO = re.compile(
    r"ticket(?:s)?\s*(?:e\.?\s*leclerc)?|carte\s*(?:e\.?\s*leclerc|fid[ée]lit[ée])|"
    r"cr[ée]dit[ée]s?|remise\s*imm[ée]diate|rembours[ée]|offert(?:e|s|es)?|gratuit(?:e|s|es)?|"
    r"\b\d{1,3}\s*%|\b-\s*\d{1,3}\s*%|\b\d+(?:[,.]\d{1,2})?\s*€|\b\d+\s*\+\s*\d+\b|2[eè]me|deuxi[èe]me",
    re.I)
PERCENT = re.compile(r"-?\s*\d{1,3}\s*%")
EURO = re.compile(r"\d+(?:[,.]\d{1,2})?\s*€")

def get(url, timeout=30):
    return requests.get(url, headers=HEADERS, timeout=timeout)

def main():
    rows, errors, pdfs = [], [], []
    try:
        response = get(CATALOG_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for a in soup.find_all("a", href=True):
            url = urljoin(response.url, a["href"])
            if url.lower().split("?")[0].endswith(".pdf") and url not in pdfs:
                pdfs.append(url)
        pdfs = pdfs[:MAX_PDFS]
        if not pdfs:
            errors.append("Aucun PDF direct détecté. Le site peut utiliser une visionneuse ou charger les catalogues dynamiquement; la collecte doit être adaptée.")
        for url in pdfs:
            try:
                r = get(url, 40)
                r.raise_for_status()
                if not r.content.startswith(b"%PDF"):
                    errors.append(f"Réponse ignorée car ce n'est pas un PDF : {url}")
                    continue
                doc = fitz.open(stream=r.content, filetype="pdf")
                for pageno, page in enumerate(doc, 1):
                    text = page.get_text("text")
                    if not text.strip():
                        rows.append({"Produit / extrait":"Page image — OCR nécessaire","Type d'offre potentiel":"À vérifier manuellement","Réduction repérée":"","Montants repérés":"","Page":pageno,"Source":url,"Texte de contexte":"","Confiance":"Faible — page sans texte extractible"})
                        continue
                    lines = [re.sub(r"\s+", " ", x).strip() for x in text.splitlines() if x.strip()]
                    for i, line in enumerate(lines):
                        if not PROMO.search(line): continue
                        context = " | ".join(lines[max(0,i-1):min(len(lines),i+2)])
                        lc = context.lower()
                        if re.search(r"ticket|carte|fid[ée]lit[ée]|cr[ée]dit", lc): kind = "Avantage fidélité potentiel"
                        elif re.search(r"offert|gratuit|\b\d+\s*\+\s*\d+\b", lc): kind = "Produit offert potentiel"
                        elif re.search(r"remise immédiate|-\s*\d+\s*%|\b\d+\s*%", lc): kind = "Réduction immédiate potentielle"
                        else: kind = "Promotion potentielle à vérifier"
                        rows.append({"Produit / extrait":line[:220],"Type d'offre potentiel":kind,"Réduction repérée":", ".join(PERCENT.findall(context)),"Montants repérés":", ".join(EURO.findall(context)),"Page":pageno,"Source":url,"Texte de contexte":context[:1500],"Confiance":"À vérifier — extraction heuristique"})
            except Exception as exc:
                errors.append(f"{url}: {type(exc).__name__}: {exc}")
    except Exception as exc:
        errors.append(f"Impossible de consulter le site: {type(exc).__name__}: {exc}")

    if not rows:
        rows.append({"Produit / extrait":"Aucune offre extraite lors de cette exécution","Type d'offre potentiel":"Diagnostic nécessaire","Réduction repérée":"","Montants repérés":"","Page":"","Source":CATALOG_URL,"Texte de contexte":"Voir l'onglet Diagnostic.","Confiance":"Aucune donnée confirmée"})
    os.makedirs("output", exist_ok=True)
    out = "output/Promotions_Leclerc.xlsx"
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(writer, index=False, sheet_name="Offres candidates")
        pd.DataFrame([{"Date UTC":datetime.now(timezone.utc).isoformat(),"Page consultée":CATALOG_URL,"PDF détectés":len(pdfs),"Messages":"\n".join(errors) if errors else "Aucune erreur technique signalée.","Note":"Offres candidates à vérifier; magasin, prix, dates et conditions non garantis."}]).to_excel(writer, index=False, sheet_name="Diagnostic")
        for ws in writer.sheets.values():
            ws.freeze_panes = "A2"; ws.auto_filter.ref = ws.dimensions
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = min(max(max(len(str(c.value or "")) for c in col)+2, 12), 60)
    print(f"Rapport créé: {out}")
    print(f"PDF directs détectés: {len(pdfs)}")
    for e in errors: print("DIAGNOSTIC:", e)

if __name__ == "__main__":
    main()
