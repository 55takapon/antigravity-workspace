from pathlib import Path
import importlib.util

source = Path(__file__).parents[1] / "20260804_phase2_retail_dx" / "collect_retailtech.py"
spec = importlib.util.spec_from_file_location("retail_collector", source)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)
collector.HERE = Path(__file__).parent
collector.LIST = "https://messe.nikkei.co.jp/exhibitor/area/FC/ja/"
collector.main()
