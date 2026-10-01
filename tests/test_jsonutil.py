import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import jsonutil as j

class JsonUtilTests(unittest.TestCase):
    def read(self,text):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.json';p.write_text(text,encoding='utf-8');return j.read_json(p)
    def test_canonical_is_order_independent(self):
        self.assertEqual(j.canonical({'b':1,'a':[2,'x']}),j.canonical({'a':[2,'x'],'b':1}))
    def test_duplicate_keys_rejected(self):
        with self.assertRaisesRegex(ValueError,'Duplicate JSON key'):self.read('{"a":1,"a":2}')
    def test_non_finite_rejected(self):
        with self.assertRaisesRegex(ValueError,'Non-finite'):self.read('{"a":NaN}')
    def test_bom_accepted(self):
        self.assertEqual(self.read('﻿{"a":1}'),{'a':1})
    def test_write_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'sub'/'x.json';j.write_json(p,{'k':'v'});self.assertEqual(j.read_json(p),{'k':'v'})
    def test_required_and_additional_properties(self):
        s={'type':'object','required':['a'],'properties':{'a':{'type':'string','minLength':1}},'additionalProperties':False}
        j.validate({'a':'x'},s)
        with self.assertRaisesRegex(ValueError,'missing a'):j.validate({},s)
        with self.assertRaisesRegex(ValueError,'not allowed'):j.validate({'a':'x','b':1},s)
        with self.assertRaisesRegex(ValueError,'empty string'):j.validate({'a':' '},s)
    def test_types_enum_pattern_bounds(self):
        with self.assertRaisesRegex(ValueError,'expected integer'):j.validate('1',{'type':'integer'})
        with self.assertRaisesRegex(ValueError,'expected integer'):j.validate(True,{'type':'integer'})
        with self.assertRaisesRegex(ValueError,'value not allowed'):j.validate('C',{'enum':['A','B']})
        with self.assertRaisesRegex(ValueError,'invalid pattern'):j.validate('x1',{'type':'string','pattern':'^[a-z]+$'})
        with self.assertRaisesRegex(ValueError,'out of range'):j.validate(9,{'type':'integer','maximum':5})
    def test_arrays(self):
        s={'type':'array','minItems':1,'maxItems':2,'uniqueItems':True,'items':{'type':'string'}}
        j.validate(['a'],s)
        with self.assertRaisesRegex(ValueError,'invalid size'):j.validate([],s)
        with self.assertRaisesRegex(ValueError,'duplicate items'):j.validate(['a','a'],s)
        with self.assertRaisesRegex(ValueError,r'\[1\]: expected string'):j.validate(['a',1],s)
    def test_any_of(self):
        s={'anyOf':[{'type':'string'},{'type':'null'}]}
        j.validate(None,s);j.validate('x',s)
        with self.assertRaisesRegex(ValueError,'no schema alternative'):j.validate(1,s)

if __name__=='__main__':unittest.main()
