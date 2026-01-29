from pyrfc import Connection

class SAPConnector:
    def __init__(self):
        self.conn = Connection(
            ashost='sap.example.com',
            sysnr='00',
            client='100',
            user='RFC_USER',
            passwd='PASSWORD'
        )
    
    def get_companies(self):
        """T001 tablosundan şirketleri çek"""
        result = self.conn.call('RFC_READ_TABLE', QUERY_TABLE='T001')
        return result['DATA']
    
    def get_products(self):
        """MARA tablosundan ürünleri çek"""
        result = self.conn.call('RFC_READ_TABLE', QUERY_TABLE='MARA')
        return result['DATA']