from abc import ABC, abstractmethod
import pandas as pd
import logging

class BaseCollector(ABC):
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f'JobHunter.{name}')
    
    @abstractmethod
    def collect(self) -> pd.DataFrame:
        pass
    
    def safe_collect(self) -> pd.DataFrame:
        try:
            df = self.collect()
            self.logger.info(f'{self.name}: {len(df)} offerte raccolte')
            return df
        except Exception as exc:
            self.logger.warning(f'{self.name}: errore - {exc}')
            return pd.DataFrame()
