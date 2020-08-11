from pathlib import Path
from tempfile import TemporaryDirectory

from tests import TestCase, ASSETS_PATH
from ocrd_browser.model import Document


class DocumentTestCase(TestCase):

    def setUp(self):
        self.path = ASSETS_PATH / 'kant_aufklaerung_1784/data/mets.xml'
        self.doc = Document.load(self.path)

    def test_get_page_ids(self):
        self.assertEqual(['PHYS_0017','PHYS_0020'], self.doc.page_ids)

    def test_reorder(self):
        self.doc.reorder(['PHYS_0020','PHYS_0017'])
        self.assertEqual(['PHYS_0020','PHYS_0017'], self.doc.page_ids)

    def test_reorder_with_wrong_ids_raises_value_error(self):
        with self.assertRaises(ValueError) as context:
            self.doc.reorder(['PHYS_0021','PHYS_0017'])

        self.assertIn('page_ids do not match', str(context.exception))

    def test_clone(self):
        doc = Document.clone(self.path)
        self.assertIn('browse-ocrd-clone-', doc.workspace.directory )
        self.assertEqual(str(self.path), doc.baseurl_mets)

        original_files = self.path.parent.rglob('*.*')
        cloned_files = Path(doc.workspace.directory).rglob('*.*')
        for original, cloned in zip(sorted(original_files), sorted(cloned_files)):
            self.assertEqual(original.read_bytes(),cloned.read_bytes())

    def test_save(self):
        doc = Document.clone(self.path)
        with TemporaryDirectory(prefix='browse-ocrd-tests') as directory:
            saved_mets = directory+'/mets.xml'
            doc.save(saved_mets)
            saved = Document.load(saved_mets)
            self.assertEqual(doc.file_groups, saved.file_groups)
            self.assertEqual(doc.page_ids, saved.page_ids)
            self.assertEqual(doc.workspace.mets.unique_identifier, saved.workspace.mets.unique_identifier)

            for page_id in doc.page_ids:
                for file_group, mime in doc.file_groups_and_mimetypes:
                    original_file = doc.file_for_page_id(page_id, file_group, mime)
                    saved_file = saved.file_for_page_id(page_id, file_group, mime)
                    self.assertEqual(original_file, saved_file)

