import importlib.util
import unittest
from datetime import datetime, timezone
from pathlib import Path
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('generator',root/'generate.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class SiteTest(unittest.TestCase):
    def test_private_filtered_and_signals_separate(self):
        data={'repositories':[{'name':'public','visibility':'public','source_url':'https://example.org/a','http_status':200,'latest_deployment':{'state':'failure'},'latest_workflow':{'conclusion':'success'},'observed_at':'2026-10-31T20:00:00Z'},{'name':'private-secret','visibility':'private','source_url':'https://example.org/secret'}]}
        out=mod.build(data,'public',datetime(2026,10,31,21,tzinfo=timezone.utc))
        self.assertNotIn('private-secret',out)
        self.assertIn('CI · success',out)
        self.assertIn('Deploy · failure',out)
        self.assertIn('HTTP · 200',out)
    def test_stale_status(self):
        data={'repositories':[{'name':'old','visibility':'public','source_url':'https://example.org/a','latest_workflow':{'conclusion':'success'},'observed_at':'2020-01-01T00:00:00Z'}]}
        self.assertIn('stale / unknown',mod.build(data,'public',datetime(2026,10,31,tzinfo=timezone.utc)))
if __name__=='__main__':unittest.main()
