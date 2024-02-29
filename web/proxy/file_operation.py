import textract
from langchain_community.document_loaders import (
    CSVLoader, Docx2txtLoader, PyPDFLoader, UnstructuredExcelLoader,
    UnstructuredWordDocumentLoader)


class FileOperation:

    def __init__(self):
        self.image_suffix = ['.jpg', '.jpeg', '.png', '.bmp']
        self.md_suffix = '.md'
        self.text_suffix = [
            '.txt', '.go', '.py', '.c', '.h', '.js', '.ts', '.text'
        ]
        self.excel_suffix = ['.xlsx', '.xls', '.csv']
        self.pdf_suffix = '.pdf'
        self.word_suffix = ['.docx', '.doc']
        self.normal_suffix = [self.md_suffix
                              ] + self.text_suffix + self.excel_suffix + [
                                  self.pdf_suffix
                              ] + self.word_suffix

    def get_type(self, filepath: str):
        if filepath.endswith(self.pdf_suffix):
            return 'pdf'

        if filepath.endswith(self.md_suffix):
            return 'md'

        for suffix in self.image_suffix:
            if filepath.endswith(suffix):
                return 'image'

        for suffix in self.text_suffix:
            if filepath.endswith(suffix):
                return 'text'

        for suffix in self.word_suffix:
            if filepath.endswith(suffix):
                return 'word'

        for suffix in self.excel_suffix:
            if filepath.endswith(suffix):
                return 'excel'
        return None

    def read(self, filepath: str):
        file_type = self.get_type(filepath)

        text = ''
        if file_type == 'md' or file_type == 'text':
            with open(filepath) as f:
                text = f.read()

        elif file_type == 'pdf':
            documents = PyPDFLoader(filepath).load()
            for document in documents:
                text += document.page_content

        elif file_type == 'excel':
            if filepath.endswith('.csv'):
                documents = CSVLoader(file_path=filepath).load()
            else:
                documents = []
                # TODO FIXME import exceptions
                # documents = UnstructuredExcelLoader(filepath, mode='elements').load()

            for document in documents:
                text += document.page_content

        elif file_type == 'word':
            # https://stackoverflow.com/questions/36001482/read-doc-file-with-python
            # https://textract.readthedocs.io/en/latest/installation.html
            text = textract.process(filepath).decode('utf8')
            print(len(text))

        text = text.replace('\n\n', '\n')
        text = text.replace('\n\n', '\n')
        text = text.replace('\n\n', '\n')
        text = text.replace('  ', ' ')
        text = text.replace('  ', ' ')
        text = text.replace('  ', ' ')
        return text


if __name__ == '__main__':
    opr = FileOperation()
    print(
        opr.read(
            '/data2/khj/HuixiangDou/web/proxy/feature_stores/9527/workdir/preprocess/技术交底书.doc'
        ))