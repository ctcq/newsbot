import json
import logging
import os

"""
Visitor class for checking chat ids to broadcast to
"""
class ChatIdVisitor():

    def __init__(self, ids_file : str):
        self.logger = logging.getLogger(__name__)        
        self.ids_file = ids_file
        self.last_modified = None
        self.chat_ids = []

    def visit(self):
        self.logger.info("Checking for new chat ids...")
        last_modified = os.stat(self.ids_file).st_mtime
        
        # Check if file hast been edited
        if not self.last_modified or last_modified < self.last_modified:
            self.logger.info("Found new chat ids")
            self.last_modified = last_modified
            with open(self.ids_file) as file:
                self.chat_ids = json.load(file) 
            
            self.logger.info(f"Now serving {len(self.chat_ids)} chat ids")
        else:
            self.logger.debug("No new chat ids found")
        
        return self.chat_ids