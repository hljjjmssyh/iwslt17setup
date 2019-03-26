import re
import sacremoses
import argparse
import os
import subprocess
import shutil

def loadAndTokenizeFile(lang, inputPath, outputPath, pattern):
    tok = sacremoses.MosesTokenizer(lang=lang)

    inputFile = open(inputPath, 'r')
    outputFile = open(outputPath, 'w')
    p = re.compile(pattern)

    for line in inputFile:
        match = p.match(line)
        if match:
            outputFile.write(tok.tokenize(match.group(1), return_str=True) + '\n')

    inputFile.close()
    outputFile.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Downloads and prepares the IWSLT2017 data set for processing')
    parser.add_argument('src', help='Source language')
    parser.add_argument('target', help='Target language')
    parser.add_argument('--path', default='./data', help='Path to the original data')
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()

    src = args.src
    target = args.target
    path = args.path
    original = f'{path}/original'


    ## Download files    
    if not os.path.exists(original):
        os.makedirs(original)

    if args.download:
        curl = subprocess.Popen(f'curl -s https://wit3.fbk.eu/archive/2017-01-trnted//texts/{src}/{target}/{src}-{target}.tgz'.split(),
                        stdout=subprocess.PIPE)
    
        tar = subprocess.Popen(f'tar xvz -C {original}'.split(), stdin=curl.stdout)
        tar.wait()

    # Load sentence pairs
    print('Reading and tokenizing training set')
    loadAndTokenizeFile(src, f'{original}/{src}-{target}/train.tags.{src}-{target}.{src}',
                             f'{path}/train.{src}',
                             r'^\s*([^<].*[^>])$')
    loadAndTokenizeFile(target, f'{original}/{src}-{target}/train.tags.{src}-{target}.{target}',
                                f'{path}/train.{target}',
                                r'^\s([^<].*[^>])$')

    print('Reading and tokenizing dev set')
    loadAndTokenizeFile(src, f'{original}/{src}-{target}/IWSLT17.TED.dev2010.{src}-{target}.{src}.xml',
                             f'{path}/dev.{src}',
                             r'^<seg id="\d+">(.*)<\/seg>')
    loadAndTokenizeFile(target, f'{original}/{src}-{target}/IWSLT17.TED.dev2010.{src}-{target}.{target}.xml',
                             f'{path}/dev.{target}',
                             r'^<seg id="\d+">(.*)<\/seg>')

    print('Reading and tokenizing test set')
    loadAndTokenizeFile(src, f'{original}/{src}-{target}/IWSLT17.TED.tst2015.{src}-{target}.{src}.xml',
                             f'{path}/tst.{src}',
                             r'^<seg id="\d+">(.*)<\/seg>')
    loadAndTokenizeFile(target, f'{original}/{src}-{target}/IWSLT17.TED.tst2015.{src}-{target}.{target}.xml',
                             f'{path}/tst.{target}',
                             r'^<seg id="\d+">(.*)<\/seg>')

    ## Apply bpe and learn vocab
    print('Learning BPE and learning vocabulary')
    subprocess.run(f'subword-nmt learn-joint-bpe-and-vocab --input {path}/train.{src} {path}/train.{target} -o {path}/codes.txt --write-vocabulary {path}/vocab.{src} {path}/vocab.{target}'.split())

    print('Finished')