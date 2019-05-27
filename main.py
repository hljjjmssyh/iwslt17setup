import re
import sacremoses
import argparse
import os
import subprocess
import html

def loadAndTokenizeFile(lang, inputPath, outputPath, pattern, append=False):
    tok = sacremoses.MosesTokenizer(lang=lang)

    inputFile = open(inputPath, 'r')
    fileRights = 'a' if append else  'w'
    outputFile = open(outputPath, fileRights)
    p = re.compile(pattern)

    for line in inputFile:
        match = p.match(line)
        if match:
            outputFile.write(html.unescape(tok.tokenize(match.group(1), return_str=True)) + '\n')

    inputFile.close()
    outputFile.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Downloads and prepares the IWSLT2017 data set for processing')
    parser.add_argument('src', help='Source language')
    parser.add_argument('target', help='Target language')
    parser.add_argument('--save_path', default='./data', help='Path where the original data and the temporal files are saved')
    parser.add_argument('--output_path', default='./data', help='Path were the final files will be saved')
    parser.add_argument('--download', action='store_true')
    parser.add_argument('--filter', action='store_true')
    parser.add_argument('--BPE', action='store_true')
    parser.add_argument('--mergeOp', default=40000, help='Number of merge operations for BPE')
    parser.add_argument('--all', action='store_true')
    args = parser.parse_args()

    src = args.src
    target = args.target
    path = args.save_path
    outPath = args.output_path
    original = f'{path}/original'


    if not os.path.exists(original):
        os.makedirs(original)

    if args.download or args.all:
        print('Downloading and extracting dataset')
        curl = subprocess.Popen(f'curl -s https://wit3.fbk.eu/archive/2017-01-trnted//texts/{src}/{target}/{src}-{target}.tgz'.split(),
                        stdout=subprocess.PIPE)

        tar = subprocess.Popen(f'tar xvz -C {original}'.split(), stdin=curl.stdout)
        tar.wait()

    # Load sentence pairs
    if args.filter or args.all:
        print('Reading and tokenizing training set')
        loadAndTokenizeFile(src, f'{original}/{src}-{target}/train.tags.{src}-{target}.{src}',
                                f'{path}/train.tok.{src}',
                                r'^\s*([^<].*[^>])$')
        loadAndTokenizeFile(target, f'{original}/{src}-{target}/train.tags.{src}-{target}.{target}',
                                    f'{path}/train.tok.{target}',
                                    r'^\s([^<].*[^>])$')

        print('Reading and tokenizing dev set')
        loadAndTokenizeFile(src, f'{original}/{src}-{target}/IWSLT17.TED.dev2010.{src}-{target}.{src}.xml',
                                f'{path}/dev.tok.{src}',
                                r'^<seg id="\d+">(.*)<\/seg>')
        loadAndTokenizeFile(target, f'{original}/{src}-{target}/IWSLT17.TED.dev2010.{src}-{target}.{target}.xml',
                                f'{path}/dev.tok.{target}',
                                r'^<seg id="\d+">(.*)<\/seg>')

        for year in range(2010, 2013):
            loadAndTokenizeFile(src, f'{original}/{src}-{target}/IWSLT17.TED.tst{year}.{src}-{target}.{src}.xml',
                                    f'{path}/dev.tok.{src}',
                                    r'^<seg id="\d+">(.*)<\/seg>', append=True)
            loadAndTokenizeFile(target, f'{original}/{src}-{target}/IWSLT17.TED.tst{year}.{src}-{target}.{target}.xml',
                                    f'{path}/dev.tok.{target}',
                                    r'^<seg id="\d+">(.*)<\/seg>', append=True)

        print('Reading and tokenizing test set')
        loadAndTokenizeFile(src, f'{original}/{src}-{target}/IWSLT17.TED.tst2013.{src}-{target}.{src}.xml',
                                f'{path}/test.tok.{src}',
                                r'^<seg id="\d+">(.*)<\/seg>')
        loadAndTokenizeFile(target, f'{original}/{src}-{target}/IWSLT17.TED.tst2013.{src}-{target}.{target}.xml',
                                f'{path}/test.tok.{target}',
                                r'^<seg id="\d+">(.*)<\/seg>')

        for year in range(2014, 2016):
            loadAndTokenizeFile(src, f'{original}/{src}-{target}/IWSLT17.TED.tst{year}.{src}-{target}.{src}.xml',
                                    f'{path}/test.tok.{src}',
                                    r'^<seg id="\d+">(.*)<\/seg>', append=True)
            loadAndTokenizeFile(target, f'{original}/{src}-{target}/IWSLT17.TED.tst{year}.{src}-{target}.{target}.xml',
                                    f'{path}/test.tok.{target}',
                                    r'^<seg id="\d+">(.*)<\/seg>', append=True)


    ## Apply bpe and learn vocab
    if args.BPE or args.all:
        print('Learning BPE and learning vocabulary')
        subprocess.run(f'subword-nmt learn-joint-bpe-and-vocab --input {path}/train.tok.{src} {path}/train.tok.{target} -s {args.mergeOp} -o {path}/codes.txt --write-vocabulary {path}/vocab.{src} {path}/vocab.{target}'.split())

        print('Applying BPE to sets')
        subprocess.Popen(f'subword-nmt apply-bpe -c {path}/codes.txt --vocabulary {path}/vocab.{src} --vocabulary-threshold 50'.split(),
                        stdin=open(f'{path}/train.tok.{src}', 'r'), stdout=open(f'{outPath}/train.{src}', 'w'))
        subprocess.Popen(f'subword-nmt apply-bpe -c {path}/codes.txt --vocabulary {path}/vocab.{target} --vocabulary-threshold 50'.split(),
                        stdin=open(f'{path}/train.tok.{target}', 'r'), stdout=open(f'{outPath}/train.{target}', 'w'))

        subprocess.Popen(f'subword-nmt apply-bpe -c {path}/codes.txt --vocabulary {path}/vocab.{src} --vocabulary-threshold 50'.split(),
                        stdin=open(f'{path}/dev.tok.{src}', 'r'), stdout=open(f'{outPath}/dev.{src}', 'w'))
        subprocess.Popen(f'subword-nmt apply-bpe -c {path}/codes.txt --vocabulary {path}/vocab.{target} --vocabulary-threshold 50'.split(),
                        stdin=open(f'{path}/dev.tok.{target}', 'r'), stdout=open(f'{outPath}/dev.{target}', 'w'))

        subprocess.Popen(f'subword-nmt apply-bpe -c {path}/codes.txt --vocabulary {path}/vocab.{src} --vocabulary-threshold 50'.split(),
                        stdin=open(f'{path}/test.tok.{src}', 'r'), stdout=open(f'{outPath}/test.{src}', 'w'))
        subprocess.Popen(f'subword-nmt apply-bpe -c {path}/codes.txt --vocabulary {path}/vocab.{target} --vocabulary-threshold 50'.split(),
                        stdin=open(f'{path}/test.tok.{target}', 'r'), stdout=open(f'{outPath}/test.{target}', 'w'))

    print('Finished')
