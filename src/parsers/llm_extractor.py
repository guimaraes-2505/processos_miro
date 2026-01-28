"""
Extrator de processos usando LLM (Claude API).
Converte transcrições em markdown para modelos estruturados de processo.
"""

import json
from typing import Dict, Optional

import anthropic
from anthropic import Anthropic

from config.settings import get_settings
from src.models.process_model import Process, ProcessExtractionResult
from src.utils.exceptions import LLMExtractionError
from src.utils.logger import get_logger

logger = get_logger()


# Prompt principal para extração de processos
EXTRACTION_PROMPT_TEMPLATE = """Você é um especialista em análise de processos de negócio. Sua tarefa é analisar uma transcrição de processo e extrair elementos estruturados.

IMPORTANTE: Esta empresa tem baixa maturidade em modelagem de processos, então use elementos SIMPLES e intuitivos:
- Tarefas: atividades que alguém executa
- Decisões: pontos onde há escolha entre caminhos
- Eventos: início e fim do processo
- Notas: observações importantes sobre o processo

TRANSCRIÇÃO:
{markdown_content}

Extraia os elementos do processo no formato JSON seguindo EXATAMENTE esta estrutura:

{{
  "process_name": "Nome claro e descritivo do processo",
  "description": "Breve descrição do que o processo faz",
  "actors": ["Lista", "de", "responsáveis/atores"],
  "elements": [
    {{
      "id": "identificador_unico",
      "type": "task",
      "name": "Nome da tarefa",
      "description": "Descrição detalhada (opcional)",
      "actor": "Nome do responsável",
      "metadata": {{}}
    }},
    {{
      "id": "gateway_1",
      "type": "gateway",
      "name": "Pergunta ou decisão a ser tomada",
      "description": "Contexto da decisão",
      "actor": "Quem decide",
      "metadata": {{
        "gateway_type": "exclusive",
        "conditions": ["Opção 1", "Opção 2", "Opção 3"]
      }}
    }},
    {{
      "id": "event_start",
      "type": "event",
      "name": "Descrição do que inicia o processo",
      "description": null,
      "actor": null,
      "metadata": {{
        "event_type": "start"
      }}
    }},
    {{
      "id": "event_end",
      "type": "event",
      "name": "Descrição do que finaliza o processo",
      "description": null,
      "actor": null,
      "metadata": {{
        "event_type": "end"
      }}
    }},
    {{
      "id": "annotation_1",
      "type": "annotation",
      "name": "Nota ou observação importante",
      "description": "Detalhes da nota",
      "actor": null,
      "metadata": {{
        "attached_to": "id_do_elemento_relacionado"
      }}
    }}
  ],
  "flows": [
    {{
      "from_element": "event_start",
      "to_element": "task_1",
      "condition": null
    }},
    {{
      "from_element": "gateway_1",
      "to_element": "task_2",
      "condition": "Se aprovado"
    }},
    {{
      "from_element": "task_3",
      "to_element": "event_end",
      "condition": null
    }}
  ]
}}

REGRAS IMPORTANTES:

1. **Tipos de elementos:**
   - "task": atividades executadas por alguém
   - "gateway": pontos de decisão (sempre com tipo "exclusive" para simplicidade)
   - "event": início ou fim do processo (event_type: "start" ou "end")
   - "annotation": notas, observações, lembretes

2. **IDs únicos:**
   - Use formato: task_1, task_2, gateway_1, event_start, event_end, annotation_1
   - IDs devem ser únicos e descritivos

3. **Atores (responsáveis):**
   - Identifique claramente quem faz cada tarefa
   - Use nomes de cargos ou departamentos
   - Eventos e anotações não têm ator (usar null)

4. **Decisões (gateways):**
   - Sempre use "exclusive" para gateway_type
   - Liste todas as opções possíveis em "conditions"
   - Cada opção deve ter um flow correspondente

5. **Fluxos (flows):**
   - Conecte elementos na ordem correta
   - Todo processo deve ter: event_start → tarefas → event_end
   - Gateways devem ter múltiplos flows de saída (um para cada condição)
   - Flows de gateways DEVEM ter "condition" preenchida

6. **Completude:**
   - Todo processo deve ter pelo menos 1 evento de início
   - Todo processo deve ter pelo menos 1 evento de fim
   - Todos os elementos devem estar conectados (alcançáveis do início)

7. **Simplicidade:**
   - Evite complexidade desnecessária
   - Use linguagem clara e direta
   - Foque no fluxo principal

Retorne APENAS o JSON válido, sem markdown, sem comentários, sem explicações adicionais.
"""


class LLMExtractor:
    """
    Extrator de processos usando Claude API.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Inicializa o extrator.

        Args:
            api_key: API key do Claude (usa settings se não fornecido)
            model: Modelo Claude a usar (usa settings se não fornecido)
        """
        settings = get_settings()

        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or settings.LLM_MODEL
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.temperature = settings.LLM_TEMPERATURE

        # Inicializar cliente Anthropic
        self.client = Anthropic(api_key=self.api_key)

        logger.info(f"LLM Extractor initialized with model: {self.model}")

    def extract(
        self,
        markdown_content: str,
        metadata: Optional[Dict] = None
    ) -> ProcessExtractionResult:
        """
        Extrai processo de uma transcrição markdown.

        Args:
            markdown_content: Conteúdo markdown pré-processado
            metadata: Metadados opcionais sobre a transcrição

        Returns:
            ProcessExtractionResult com processo extraído

        Raises:
            LLMExtractionError: Se falhar ao extrair ou parsear resposta
        """
        logger.info("Starting LLM extraction...")

        # Criar prompt com conteúdo
        prompt = EXTRACTION_PROMPT_TEMPLATE.format(
            markdown_content=markdown_content
        )

        try:
            # Chamar Claude API
            logger.debug(f"Calling Claude API (model={self.model})...")
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extrair resposta
            response_text = message.content[0].text
            logger.debug(f"Received response ({len(response_text)} chars)")

            # Parse JSON
            try:
                process_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response: {response_text[:500]}...")
                raise LLMExtractionError(
                    f"Invalid JSON response from LLM: {e}",
                    raw_response=response_text,
                    model=self.model
                )

            # Criar modelo Process
            try:
                process = Process(**process_data)
            except Exception as e:
                logger.error(f"Failed to create Process model: {e}")
                logger.error(f"Data: {process_data}")
                raise LLMExtractionError(
                    f"Invalid process data structure: {e}",
                    raw_response=response_text,
                    model=self.model
                )

            # Criar resultado
            result = ProcessExtractionResult(
                process=process,
                source_file=metadata.get('file_path') if metadata else None,
                llm_model=self.model,
                warnings=[]
            )

            logger.info(f"Successfully extracted process: {process.name}")
            logger.info(f"  - {len(process.elements)} elements")
            logger.info(f"  - {len(process.flows)} flows")
            logger.info(f"  - {len(process.actors)} actors")

            return result

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise LLMExtractionError(
                f"API error: {e}",
                model=self.model
            )
        except Exception as e:
            if isinstance(e, LLMExtractionError):
                raise
            logger.error(f"Unexpected error during extraction: {e}")
            raise LLMExtractionError(
                f"Extraction failed: {e}",
                model=self.model
            )

    def extract_with_retry(
        self,
        markdown_content: str,
        metadata: Optional[Dict] = None,
        max_retries: int = 3
    ) -> ProcessExtractionResult:
        """
        Extrai processo com retry automático em caso de falha.

        Args:
            markdown_content: Conteúdo markdown
            metadata: Metadados opcionais
            max_retries: Número máximo de tentativas

        Returns:
            ProcessExtractionResult

        Raises:
            LLMExtractionError: Se todas as tentativas falharem
        """
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Extraction attempt {attempt}/{max_retries}")
                return self.extract(markdown_content, metadata)
            except LLMExtractionError as e:
                last_error = e
                if attempt < max_retries:
                    logger.warning(f"Attempt {attempt} failed, retrying...")
                else:
                    logger.error(f"All {max_retries} attempts failed")

        # Se chegou aqui, todas as tentativas falharam
        raise last_error


def extract_process_from_markdown(
    markdown_content: str,
    metadata: Optional[Dict] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> ProcessExtractionResult:
    """
    Função utilitária para extrair processo de markdown.

    Args:
        markdown_content: Conteúdo markdown
        metadata: Metadados opcionais
        api_key: API key do Claude (opcional)
        model: Modelo Claude (opcional)

    Returns:
        ProcessExtractionResult
    """
    extractor = LLMExtractor(api_key=api_key, model=model)
    return extractor.extract(markdown_content, metadata)
