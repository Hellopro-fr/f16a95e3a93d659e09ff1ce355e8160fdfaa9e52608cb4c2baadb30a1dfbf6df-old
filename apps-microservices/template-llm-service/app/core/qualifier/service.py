import json
import re
from vllm import LLM, SamplingParams
from app.core.qualifier.utils import PROMPT_TEMPLATE_FR
from bs4 import BeautifulSoup # <-- Importez BeautifulSoup

class QualifierService:
    def __init__(self):
        self.llm_args = {
            "model": "Qwen/Qwen2.5-14B-Instruct", 
            "quantization": "awq",              
            "gpu_memory_utilization": 0.90,
            "trust_remote_code": True,
            "dtype": "auto"
        }
        self.llm = LLM(**self.llm_args)
        self.tokenizer = self.llm.get_tokenizer()

    def classify(self, url: str, content: str):
        if not content:
            return "contenu_vide", None, {"url": url}

        # --- ÉTAPE DE NETTOYAGE DU CONTENU HTML ---
        # 1. Parser le HTML avec BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')

        # 2. Supprimer les balises inutiles et bruyantes (scripts, styles, etc.)
        for script_or_style in soup(["script", "style", "header", "footer", "nav", "aside"]):
            script_or_style.decompose()

        # 3. Extraire uniquement le texte propre et lisible
        cleaned_text = soup.get_text(separator='\n', strip=True)
        
        # 4. Tronquer le contenu pour s'assurer qu'il n'est pas trop long (sécurité)
        #    On garde les 15 000 premiers caractères, ce qui est largement suffisant.
        truncated_content = cleaned_text[:15000]
        # --- FIN DU NETTOYAGE ---

        sampling_params = SamplingParams(max_tokens=250, temperature=0.1)

        # On utilise le contenu nettoyé et tronqué dans le prompt
        user_prompt = PROMPT_TEMPLATE_FR.format(url=url, content=truncated_content)
        
        conversation = [{"role": "user", "content": user_prompt}]
        
        formatted_prompt = self.tokenizer.apply_chat_template(
            conversation, 
            tokenize=False, 
            add_generation_prompt=True
        )

        outputs = self.llm.generate([formatted_prompt], sampling_params)
        raw_text = outputs[0].outputs[0].text.strip()

        # Le bloc de parsing robuste avec Regex reste essentiel
        try:
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                json_string = match.group(0)
                result = json.loads(json_string)
            else:
                raise ValueError("Aucun bloc JSON trouvé dans la sortie du LLM.")
        except (json.JSONDecodeError, ValueError) as e:
            print("--- ERREUR DE PARSING JSON ---")
            print(f"Erreur: {e}")
            print(f"Sortie brute du LLM: '{raw_text}'")
            result = {
                "type_page": "erreur_parsing",
                "chunk": None,
                "metadata": {"raw_output": raw_text}
            }
            
        chunk = content[:500] # On renvoie toujours un bout du contenu original
        metadata = {"url": url}
        return result.get("type_page", "N/A"), chunk, metadata
