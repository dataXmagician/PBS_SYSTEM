"""
Connection Manager - Dis kaynak baglanti yoneticisi

SAP OData, HANA DB ve dosya kaynaklar icin baglanti testi,
ornek veri cekme ve tam veri cekme islemlerini yonetir.
"""

import logging
import io
from typing import Tuple, List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Dis kaynak baglanti islemlerini yoneten sinif."""

    # ============ Test Connection ============

    @staticmethod
    def test_connection(conn_type: str, config: dict) -> dict:
        """
        Baglanti testini calistirir.
        Returns: {"success": bool, "message": str, "details": dict|None}
        """
        try:
            if conn_type == "sap_odata":
                return ConnectionManager._test_sap_odata(config)
            elif conn_type == "hana_db":
                return ConnectionManager._test_hana_db(config)
            elif conn_type == "file_upload":
                return {"success": True, "message": "Dosya yukleme baglantisi test gerektirmez.", "details": None}
            else:
                return {"success": False, "message": f"Bilinmeyen baglanti tipi: {conn_type}", "details": None}
        except Exception as e:
            logger.error(f"Baglanti testi hatasi ({conn_type}): {e}")
            return {"success": False, "message": f"Baglanti hatasi: {str(e)}", "details": None}

    @staticmethod
    def _test_sap_odata(config: dict) -> dict:
        """SAP OData baglanti testi."""
        import requests
        from requests.auth import HTTPBasicAuth

        host = config.get("host", "").rstrip("/")
        username = config.get("username", "")
        password = config.get("password", "")
        sap_client = config.get("sap_client", "")
        sap_service_path = config.get("sap_service_path", "")

        if not host:
            return {"success": False, "message": "SAP host adresi gerekli.", "details": None}

        # OData service metadata'sini cek
        url = f"{host}{sap_service_path}/$metadata"
        headers = {"Accept": "application/xml"}
        if sap_client:
            headers["sap-client"] = sap_client

        auth = HTTPBasicAuth(username, password) if username else None

        try:
            resp = requests.get(url, headers=headers, auth=auth, timeout=15, verify=False)
            if resp.status_code == 200:
                return {
                    "success": True,
                    "message": "SAP OData baglantisi basarili.",
                    "details": {"status_code": resp.status_code, "url": url}
                }
            else:
                return {
                    "success": False,
                    "message": f"SAP OData hatasi: HTTP {resp.status_code}",
                    "details": {"status_code": resp.status_code, "body": resp.text[:500]}
                }
        except requests.exceptions.ConnectionError as e:
            return {"success": False, "message": f"Baglanti kurulamadi: {str(e)}", "details": None}
        except requests.exceptions.Timeout:
            return {"success": False, "message": "Baglanti zaman asimina ugradi (15s).", "details": None}

    @staticmethod
    def _test_hana_db(config: dict) -> dict:
        """HANA DB baglanti testi."""
        try:
            from hdbcli import dbapi
        except ImportError:
            return {
                "success": False,
                "message": "hdbcli modulu yuklu degil. pip install hdbcli gerekli.",
                "details": None
            }

        host = config.get("host", "")
        port = config.get("port", 443)
        database_name = config.get("database_name", "")
        username = config.get("username", "")
        password = config.get("password", "")

        if not host or not username:
            return {"success": False, "message": "HANA host ve kullanici adi gerekli.", "details": None}

        try:
            conn = dbapi.connect(
                address=host,
                port=port,
                user=username,
                password=password,
                databaseName=database_name if database_name else None,
                encrypt=True,
                sslValidateCertificate=False
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM DUMMY")
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result and result[0] == 1:
                return {
                    "success": True,
                    "message": "HANA DB baglantisi basarili.",
                    "details": {"host": host, "port": port}
                }
            return {"success": False, "message": "HANA DB test sorgusu beklenmedik sonuc verdi.", "details": None}
        except Exception as e:
            return {"success": False, "message": f"HANA DB hatasi: {str(e)}", "details": None}

    # ============ Fetch Sample Data ============

    @staticmethod
    def fetch_sample_data(
        conn_type: str,
        config: dict,
        query_config: dict,
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Ornek veri ceker (kolon tespiti icin).
        Returns: (rows, column_names)
        """
        if conn_type == "sap_odata":
            return ConnectionManager._fetch_sap_sample(config, query_config, limit)
        elif conn_type == "hana_db":
            return ConnectionManager._fetch_hana_sample(config, query_config, limit)
        elif conn_type == "file_upload":
            return ConnectionManager._fetch_file_sample(query_config, limit)
        else:
            raise ValueError(f"Bilinmeyen baglanti tipi: {conn_type}")

    @staticmethod
    def _fetch_sap_sample(config: dict, query_config: dict, limit: int) -> Tuple[List[Dict], List[str]]:
        """SAP OData'dan ornek veri ceker."""
        import requests
        from requests.auth import HTTPBasicAuth

        host = config.get("host", "").rstrip("/")
        sap_service_path = config.get("sap_service_path", "")
        entity = query_config.get("odata_entity", "")
        select = query_config.get("odata_select", "")
        filter_str = query_config.get("odata_filter", "")
        top = query_config.get("odata_top") or limit

        if not entity:
            raise ValueError("OData entity set belirtilmeli.")

        # URL olustur
        url = f"{host}{sap_service_path}/{entity}"
        params = {"$format": "json", "$top": str(min(top, limit))}
        if select:
            params["$select"] = select
        if filter_str:
            params["$filter"] = filter_str

        headers = {"Accept": "application/json"}
        sap_client = config.get("sap_client", "")
        if sap_client:
            headers["sap-client"] = sap_client

        username = config.get("username", "")
        password = config.get("password", "")
        auth = HTTPBasicAuth(username, password) if username else None

        resp = requests.get(url, params=params, headers=headers, auth=auth, timeout=30, verify=False)
        resp.raise_for_status()

        data = resp.json()
        results = data.get("d", {}).get("results", [])
        if not results:
            # Bazi OData servisleri d.results yerine value donebilir
            results = data.get("value", [])
        if not results:
            return [], []

        # __metadata gibi meta alanlari filtrele
        rows = []
        for r in results:
            row = {k: v for k, v in r.items() if not k.startswith("__")}
            rows.append(row)

        column_names = list(rows[0].keys()) if rows else []
        return rows, column_names

    @staticmethod
    def _fetch_hana_sample(config: dict, query_config: dict, limit: int) -> Tuple[List[Dict], List[str]]:
        """HANA DB'den ornek veri ceker."""
        from hdbcli import dbapi

        query_text = query_config.get("query_text", "")
        if not query_text:
            raise ValueError("HANA sorgu metni gerekli.")

        conn = dbapi.connect(
            address=config.get("host", ""),
            port=config.get("port", 443),
            user=config.get("username", ""),
            password=config.get("password", ""),
            databaseName=config.get("database_name") or None,
            encrypt=True,
            sslValidateCertificate=False
        )

        try:
            cursor = conn.cursor()
            # LIMIT ekle (eger yoksa)
            sql = query_text.rstrip().rstrip(";")
            if "LIMIT" not in sql.upper():
                sql = f"SELECT * FROM ({sql}) AS sub LIMIT {limit}"
            cursor.execute(sql)

            column_names = [desc[0] for desc in cursor.description]
            raw_rows = cursor.fetchall()
            rows = []
            for raw_row in raw_rows:
                row = {}
                for i, col_name in enumerate(column_names):
                    val = raw_row[i]
                    row[col_name] = str(val) if val is not None else None
                rows.append(row)

            cursor.close()
            return rows, column_names
        finally:
            conn.close()

    @staticmethod
    def _fetch_file_sample(query_config: dict, limit: int) -> Tuple[List[Dict], List[str]]:
        """Dosya iceriginden ornek veri ceker. file_bytes query_config icinde olmali."""
        import pandas as pd

        file_bytes = query_config.get("file_bytes")
        file_name = query_config.get("file_name", "")
        parse_config = query_config.get("file_parse_config") or {}

        if file_bytes is None:
            raise ValueError("Dosya icerigi gerekli.")

        df = ConnectionManager._read_file_to_dataframe(file_bytes, file_name, parse_config)
        df = df.head(limit)

        # NaN degerleri None yap
        df = df.where(df.notna(), None)

        rows = df.to_dict(orient="records")
        column_names = list(df.columns)

        # Tum degerleri string'e cevir
        for row in rows:
            for k, v in row.items():
                row[k] = str(v) if v is not None else None

        return rows, column_names

    # ============ Fetch All Data ============

    @staticmethod
    def fetch_all_data(conn_type: str, config: dict, query_config: dict) -> List[Dict[str, Any]]:
        """Tum veriyi ceker (sync icin)."""
        if conn_type == "sap_odata":
            return ConnectionManager._fetch_sap_all(config, query_config)
        elif conn_type == "hana_db":
            return ConnectionManager._fetch_hana_all(config, query_config)
        elif conn_type == "file_upload":
            rows, _ = ConnectionManager._fetch_file_sample(query_config, limit=1_000_000)
            return rows
        else:
            raise ValueError(f"Bilinmeyen baglanti tipi: {conn_type}")

    @staticmethod
    def _fetch_sap_all(config: dict, query_config: dict) -> List[Dict]:
        """SAP OData'dan tum veriyi ceker (pagination ile)."""
        import requests
        from requests.auth import HTTPBasicAuth

        host = config.get("host", "").rstrip("/")
        sap_service_path = config.get("sap_service_path", "")
        entity = query_config.get("odata_entity", "")
        select = query_config.get("odata_select", "")
        filter_str = query_config.get("odata_filter", "")
        top = query_config.get("odata_top")

        url = f"{host}{sap_service_path}/{entity}"
        params = {"$format": "json"}
        if select:
            params["$select"] = select
        if filter_str:
            params["$filter"] = filter_str
        if top:
            params["$top"] = str(top)

        headers = {"Accept": "application/json"}
        sap_client = config.get("sap_client", "")
        if sap_client:
            headers["sap-client"] = sap_client

        username = config.get("username", "")
        password = config.get("password", "")
        auth = HTTPBasicAuth(username, password) if username else None

        all_rows = []
        current_url = url
        current_params = params

        while current_url:
            resp = requests.get(current_url, params=current_params, headers=headers, auth=auth, timeout=60, verify=False)
            resp.raise_for_status()
            data = resp.json()

            results = data.get("d", {}).get("results", [])
            if not results:
                results = data.get("value", [])

            for r in results:
                row = {k: str(v) if v is not None else None for k, v in r.items() if not k.startswith("__")}
                all_rows.append(row)

            # Pagination: __next veya @odata.nextLink
            next_link = data.get("d", {}).get("__next") or data.get("@odata.nextLink")
            if next_link and not top:
                current_url = next_link
                current_params = {}  # next_link zaten parametreleri icerir
            else:
                current_url = None

        return all_rows

    @staticmethod
    def _fetch_hana_all(config: dict, query_config: dict) -> List[Dict]:
        """HANA DB'den tum veriyi ceker."""
        from hdbcli import dbapi

        query_text = query_config.get("query_text", "")
        if not query_text:
            raise ValueError("HANA sorgu metni gerekli.")

        conn = dbapi.connect(
            address=config.get("host", ""),
            port=config.get("port", 443),
            user=config.get("username", ""),
            password=config.get("password", ""),
            databaseName=config.get("database_name") or None,
            encrypt=True,
            sslValidateCertificate=False
        )

        try:
            cursor = conn.cursor()
            sql = query_text.rstrip().rstrip(";")
            cursor.execute(sql)

            column_names = [desc[0] for desc in cursor.description]
            raw_rows = cursor.fetchall()
            rows = []
            for raw_row in raw_rows:
                row = {}
                for i, col_name in enumerate(column_names):
                    val = raw_row[i]
                    row[col_name] = str(val) if val is not None else None
                rows.append(row)

            cursor.close()
            return rows
        finally:
            conn.close()

    # ============ Helper: File Reading ============

    # Turk dili ve Bati Avrupa karakter setleri icin encoding fallback sirasi
    ENCODING_FALLBACK_ORDER = ["utf-8", "utf-8-sig", "iso-8859-9", "cp1254", "latin1"]

    @staticmethod
    def _read_csv_with_encoding_fallback(
        file_bytes: bytes, delimiter: str, header, encoding_hint: str | None = None
    ):
        """
        CSV/TXT dosyasini okur. encoding_hint verilmemisse veya 'auto' ise
        birden fazla encoding dener (UTF-8 > UTF-8 BOM > ISO-8859-9 > CP1254 > Latin1).
        Turkce karakterler (ş, ğ, ı, ö, ü, ç) icin otomatik tespit saglar.
        """
        import pandas as pd

        # Kullanici acikca encoding belirttiyse sadece onu dene
        if encoding_hint and encoding_hint.lower() not in ("auto", ""):
            buffer = io.BytesIO(file_bytes)
            return pd.read_csv(buffer, delimiter=delimiter, encoding=encoding_hint, header=header, dtype=str)

        # Otomatik encoding tespiti: sirayla dene
        last_error = None
        for enc in ConnectionManager.ENCODING_FALLBACK_ORDER:
            try:
                buffer = io.BytesIO(file_bytes)
                df = pd.read_csv(buffer, delimiter=delimiter, encoding=enc, header=header, dtype=str)
                logger.info(f"CSV dosyasi '{enc}' encoding ile basariyla okundu")
                return df
            except (UnicodeDecodeError, UnicodeError) as e:
                last_error = e
                logger.debug(f"Encoding '{enc}' basarisiz: {e}")
                continue

        # Hicbiri calismadiysa son hatayi ver
        raise last_error or ValueError("Dosya encoding'i tespit edilemedi")

    @staticmethod
    def _read_file_to_dataframe(file_bytes: bytes, file_name: str, parse_config: dict):
        """Dosya icerigini pandas DataFrame'e donusturur."""
        import pandas as pd

        file_ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
        delimiter = parse_config.get("delimiter", ";")
        encoding = parse_config.get("encoding", None)
        has_header = parse_config.get("has_header", True)
        sheet_name = parse_config.get("sheet_name", 0)

        header = 0 if has_header else None

        if file_ext in ("csv", "txt"):
            df = ConnectionManager._read_csv_with_encoding_fallback(
                file_bytes, delimiter, header, encoding_hint=encoding
            )
        elif file_ext in ("xlsx", "xls"):
            buffer = io.BytesIO(file_bytes)
            df = pd.read_excel(buffer, sheet_name=sheet_name, header=header, dtype=str)
        elif file_ext == "parquet":
            buffer = io.BytesIO(file_bytes)
            df = pd.read_parquet(buffer)
            # Parquet veri tiplerini korur, string'e cevirmeye gerek yok
        else:
            # Varsayilan: CSV olarak dene (encoding fallback ile)
            df = ConnectionManager._read_csv_with_encoding_fallback(
                file_bytes, delimiter, header, encoding_hint=encoding
            )

        # Header yoksa kolon isimlerini olustur
        if not has_header:
            df.columns = [f"column_{i+1}" for i in range(len(df.columns))]

        return df
