"""
数据整合与回填模块

功能：
1. 跨表合并（以 CAS + INCI 为主键）
2. 状态优先层级处理（Prohibited > Restricted > Allowed > Listed）
3. 回填"未规定"状态
4. 生成统一的多国法规数据库
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
from datetime import datetime

from schema.database_schema import (
    Jurisdiction,
    Status,
    BaseRegulationRecord,
    ProhibitedRecord,
    RestrictedRecord,
    AllowedPreservativeRecord,
    AllowedUVFilterRecord,
    AllowedColorantRecord,
    GeneralWhitelistRecord,
    TABLE_TYPES,
    create_not_specified_record,
)

logger = logging.getLogger(__name__)


# 状态优先级（数字越小优先级越高）
STATUS_PRIORITY = {
    Status.PROHIBITED: 1,
    Status.RESTRICTED: 2,
    Status.ALLOWED: 3,
    Status.LISTED: 4,
    Status.NOT_LISTED: 5,
    Status.NOT_SPECIFIED: 6,
}


class DataIntegrator:
    """数据整合器

    负责整合来自不同法规属地的解析数据，并生成统一的多表数据库。
    """

    def __init__(self, output_dir: Path):
        """
        初始化数据整合器

        Args:
            output_dir: 输出目录（用于保存整合后的数据）
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 六张主表的数据
        self.tables: Dict[str, List[BaseRegulationRecord]] = {
            "prohibited": [],
            "restricted": [],
            "preservatives": [],
            "uv_filters": [],
            "colorants": [],
            "whitelist": [],
        }

        # 成分索引：(INCI_Name, CAS_No) -> Set[table_types]
        # 用于跟踪每个成分在哪些表中出现
        self.ingredient_index: Dict[Tuple[str, Optional[str]], Set[str]] = defaultdict(set)

        # 法规属地统计
        self.jurisdiction_stats: Dict[Jurisdiction, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

    def add_records(
        self,
        table_type: str,
        records: List[BaseRegulationRecord]
    ) -> None:
        """
        添加记录到相应的表

        Args:
            table_type: 表类型（prohibited, restricted, preservatives, uv_filters, colorants, whitelist）
            records: 记录列表
        """
        if table_type not in TABLE_TYPES:
            raise ValueError(f"Invalid table type: {table_type}")

        for record in records:
            # 添加到表
            self.tables[table_type].append(record)

            # 更新索引
            key = (record.INCI_Name, record.CAS_No)
            self.ingredient_index[key].add(table_type)

            # 更新统计
            if record.Status != Status.NOT_SPECIFIED:
                self.jurisdiction_stats[record.Jurisdiction][table_type] += 1

        logger.info(
            f"Added {len(records)} records to {table_type} table"
        )

    def resolve_conflicts(self) -> None:
        """
        解决冲突：同一成分在同一法规属地的多个表中出现

        优先级规则：Prohibited > Restricted > Allowed > Listed

        如果同一成分在同一法规属地出现在多个表中，保留优先级最高的记录，
        其他记录标记为冲突或删除。
        """
        # 按 (Jurisdiction, INCI_Name, CAS_No) 分组
        conflicts: Dict[
            Tuple[Jurisdiction, str, Optional[str]],
            List[Tuple[str, BaseRegulationRecord]]
        ] = defaultdict(list)

        # 收集所有记录
        for table_type, records in self.tables.items():
            for record in records:
                key = (record.Jurisdiction, record.INCI_Name, record.CAS_No)
                conflicts[key].append((table_type, record))

        # 处理冲突
        resolved_count = 0
        for key, entries in conflicts.items():
            if len(entries) <= 1:
                continue  # 无冲突

            jurisdiction, inci_name, cas_no = key

            # 按状态优先级排序
            entries.sort(key=lambda x: STATUS_PRIORITY.get(x[1].Status, 99))

            # 保留优先级最高的记录
            kept_table, kept_record = entries[0]

            # 标记其他记录
            for table_type, record in entries[1:]:
                # 在 Notes 中添加冲突信息
                conflict_note = (
                    f"冲突: 该成分在 {kept_table} 表中状态为 {kept_record.Status.value}，"
                    f"优先级更高"
                )
                if record.Notes:
                    record.Notes += f" | {conflict_note}"
                else:
                    record.Notes = conflict_note

                logger.debug(
                    f"Conflict resolved for {inci_name} ({cas_no}) in {jurisdiction}: "
                    f"Kept {kept_record.Status.value} from {kept_table}, "
                    f"marked {record.Status.value} from {table_type}"
                )
                resolved_count += 1

        if resolved_count > 0:
            logger.info(f"Resolved {resolved_count} conflicts")

    def backfill_not_specified(self) -> None:
        """
        回填"未规定"记录

        对于每个成分，检查是否在所有法规属地的所有相关表中都有记录。
        如果缺失，则创建"未规定"记录。
        """
        # 收集所有独特的成分
        all_ingredients: Set[Tuple[str, Optional[str]]] = set()

        for table_type, records in self.tables.items():
            for record in records:
                all_ingredients.add((record.INCI_Name, record.CAS_No))

        logger.info(f"Found {len(all_ingredients)} unique ingredients")

        # 对于每个成分，检查是否在所有法规属地和表中都有记录
        backfilled_count = 0

        for inci_name, cas_no in all_ingredients:
            # 检查每个法规属地
            for jurisdiction in Jurisdiction:
                # 检查每个表
                for table_type in TABLE_TYPES.keys():
                    # 检查是否已存在记录
                    exists = any(
                        r.Jurisdiction == jurisdiction
                        and r.INCI_Name == inci_name
                        and r.CAS_No == cas_no
                        for r in self.tables[table_type]
                    )

                    # 如果不存在，创建"未规定"记录
                    if not exists:
                        not_specified_record = create_not_specified_record(
                            inci_name=inci_name,
                            cas_no=cas_no,
                            jurisdiction=jurisdiction,
                            table_type=table_type,
                        )
                        self.tables[table_type].append(not_specified_record)
                        backfilled_count += 1

        logger.info(f"Backfilled {backfilled_count} 'Not Specified' records")

    def generate_master_view(self) -> List[Dict]:
        """
        生成主视图（MasterView）

        主视图包含所有成分在所有法规属地的汇总信息，
        便于前端进行多国比对。

        Returns:
            主视图数据列表
        """
        master_view = []

        # 收集所有独特的成分
        all_ingredients: Set[Tuple[str, Optional[str]]] = set()

        for table_type, records in self.tables.items():
            for record in records:
                all_ingredients.add((record.INCI_Name, record.CAS_No))

        # 对于每个成分，汇总所有法规属地的信息
        for inci_name, cas_no in sorted(all_ingredients):
            ingredient_data = {
                "INCI_Name": inci_name,
                "CAS_No": cas_no,
                "Regulations": {}
            }

            # 收集每个法规属地的信息
            for jurisdiction in Jurisdiction:
                jurisdiction_data = {}

                # 收集该成分在该法规属地的所有记录
                for table_type, records in self.tables.items():
                    matching_records = [
                        r for r in records
                        if r.Jurisdiction == jurisdiction
                        and r.INCI_Name == inci_name
                        and r.CAS_No == cas_no
                    ]

                    if matching_records:
                        # 取状态优先级最高的记录
                        matching_records.sort(
                            key=lambda x: STATUS_PRIORITY.get(x.Status, 99)
                        )
                        primary_record = matching_records[0]

                        jurisdiction_data = {
                            "Status": primary_record.Status.value,
                            "Max_Conc_Percent": primary_record.Max_Conc_Percent,
                            "Product_Type": (
                                primary_record.Product_Type.value
                                if primary_record.Product_Type
                                else None
                            ),
                            "Conditions": primary_record.Conditions,
                            "Legal_Basis": primary_record.Legal_Basis,
                            "Update_Date": (
                                primary_record.Update_Date.isoformat()
                                if primary_record.Update_Date
                                else None
                            ),
                            "Notes": primary_record.Notes,
                        }
                        break

                # 如果没有找到任何记录，标记为"未规定"
                if not jurisdiction_data:
                    jurisdiction_data = {"Status": "未规定"}

                ingredient_data["Regulations"][jurisdiction.value] = jurisdiction_data

            master_view.append(ingredient_data)

        logger.info(f"Generated master view with {len(master_view)} ingredients")
        return master_view

    def save_tables(self) -> None:
        """
        保存所有表到文件

        每个表保存为独立的 JSON 文件。
        """
        timestamp = datetime.now().isoformat()

        for table_type, records in self.tables.items():
            # 转换为字典列表
            data = {
                "table_type": table_type,
                "generated_at": timestamp,
                "total_records": len(records),
                "records": [r.to_dict() for r in records]
            }

            # 保存到文件
            output_file = self.output_dir / f"{table_type}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved {len(records)} records to {output_file}")

    def save_master_view(self, master_view: List[Dict]) -> None:
        """
        保存主视图到文件

        Args:
            master_view: 主视图数据
        """
        output_file = self.output_dir / "master_view.json"

        data = {
            "generated_at": datetime.now().isoformat(),
            "total_ingredients": len(master_view),
            "jurisdictions": [j.value for j in Jurisdiction],
            "data": master_view
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved master view with {len(master_view)} ingredients to {output_file}")

    def generate_statistics(self) -> Dict:
        """
        生成统计信息

        Returns:
            统计信息字典
        """
        stats = {
            "tables": {},
            "jurisdictions": {},
            "total_ingredients": len(self.ingredient_index),
        }

        # 表统计
        for table_type, records in self.tables.items():
            stats["tables"][table_type] = {
                "total": len(records),
                "by_jurisdiction": {}
            }

            for jurisdiction in Jurisdiction:
                count = sum(
                    1 for r in records
                    if r.Jurisdiction == jurisdiction
                    and r.Status != Status.NOT_SPECIFIED
                )
                stats["tables"][table_type]["by_jurisdiction"][jurisdiction.value] = count

        # 法规属地统计
        for jurisdiction in Jurisdiction:
            stats["jurisdictions"][jurisdiction.value] = dict(
                self.jurisdiction_stats[jurisdiction]
            )

        return stats

    def save_statistics(self, stats: Dict) -> None:
        """
        保存统计信息到文件

        Args:
            stats: 统计信息
        """
        output_file = self.output_dir / "statistics.json"

        data = {
            "generated_at": datetime.now().isoformat(),
            "statistics": stats
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved statistics to {output_file}")

    def integrate(self) -> None:
        """
        执行完整的数据整合流程

        1. 解决冲突
        2. 回填"未规定"记录
        3. 生成主视图
        4. 保存所有表
        5. 生成和保存统计信息
        """
        logger.info("Starting data integration...")

        # 1. 解决冲突
        self.resolve_conflicts()

        # 2. 回填"未规定"记录
        self.backfill_not_specified()

        # 3. 生成主视图
        master_view = self.generate_master_view()

        # 4. 保存所有表
        self.save_tables()

        # 5. 保存主视图
        self.save_master_view(master_view)

        # 6. 生成和保存统计信息
        stats = self.generate_statistics()
        self.save_statistics(stats)

        logger.info("Data integration completed successfully!")


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    # 创建测试数据
    integrator = DataIntegrator(output_dir=Path("data/integrated"))

    # 添加测试记录
    test_records = [
        ProhibitedRecord(
            INCI_Name="Formaldehyde",
            CAS_No="50-00-0",
            Jurisdiction=Jurisdiction.EU,
        ),
        RestrictedRecord(
            INCI_Name="Triclosan",
            CAS_No="3380-34-5",
            Jurisdiction=Jurisdiction.EU,
            Max_Conc_Percent=0.3,
        ),
    ]

    integrator.add_records("prohibited", [test_records[0]])
    integrator.add_records("restricted", [test_records[1]])

    # 执行整合
    integrator.integrate()
