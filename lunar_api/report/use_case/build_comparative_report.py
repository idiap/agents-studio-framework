# Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

class BuildComparativeReportUseCase:
    pass
    # def __init__(
    #     self,
    #     knowledge_base_repository: KnowledgeBaseRepository,
    #     runner: Runner,
    #     context: Context,
    #     model: str,
    # ):
    #     self.knowledge_base_repository = knowledge_base_repository
    #     self._runner = runner
    #     self._context = context
    #     self.model = model

    # async def execute(self):
    #     jpm_id = UUID("3129e817-39d4-4f1f-aef3-fbbe3308ac1b")
    #     ft_id = UUID("fbb6a347-f565-4ef1-bc67-06a3ea71413a")
    #     nt_id = UUID("54c9ce18-9e96-49d9-bd2b-fb48ff50d3ed")
    #     horizon_id = UUID("cbf5a981-646a-43a6-9dbf-4aa554469ade")
    #     jpm_content = self.knowledge_base_repository.get_file_by_id(jpm_id)
    #     ft_content = self.knowledge_base_repository.get_file_by_id(ft_id)
    #     nt_content = self.knowledge_base_repository.get_file_by_id(nt_id)
    #     horizon_content = self.knowledge_base_repository.get_file_by_id(horizon_id)

    #     if not jpm_content or not ft_content or not nt_content or not horizon_content:
    #         raise ValueError("Report not found.")

    #     from markitdown import MarkItDown
    #     from io import BytesIO

    #     md = MarkItDown()
    #     jpm_content = md.convert(BytesIO(jpm_content.content))
    #     ft_content = md.convert(BytesIO(ft_content.content))
    #     nt_content = md.convert(BytesIO(nt_content.content))
    #     horizon_content = md.convert(BytesIO(horizon_content.content))
    #     result = await self._runner.run(
    #         report_insights_flow,
    #         inputs={
    #             "jpm_report_content": jpm_content.text_content,
    #             "ft_report_content": ft_content.text_content,
    #             "nt_report_content": nt_content.text_content,
    #             "horizon_report_content": horizon_content.text_content,
    #         },
    #     )
    #     if result.value is None:
    #         raise ValueError("Flow execution returned no result.")
    #     storage_connection: PostgresConnection = self._context.get(
    #         storage_connection_token.token
    #     )
    #     saved_report = storage_connection.execute(
    #         """
    #         INSERT INTO reports (name, content, created_at)
    #         VALUES (%(title)s, %(content)s, NOW())
    #         RETURNING id, name, content, created_at
    #         """,
    #         {"title": "Report", "content": result.value["contrast_generator"].value},
    #         commit=True,
    #         mode=ExecuteMode.FETCH_ONE,
    #     )
    #     if not saved_report or len(saved_report) == 0:
    #         raise ValueError("Failed to save the report.")
    #     return saved_report[0]
