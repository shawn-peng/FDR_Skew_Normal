#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 18 11:12:00 2020

@author: yisupeng
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar  1 22:10:26 2020

@author: yisupeng
"""

import os
import tarfile

import csv
import numpy as np
import matplotlib.pyplot as plt

import json


#%%

#species = 'c_elegans'
#species = 'drosophila'
#species = 'e_coli'
#species = 'human'
#species = 'mouse'
#species = 'yeast'


species_list = [
        'c_elegans',
        'drosophila',
        'e_coli',
        'human',
        'mouse',
        'yeast',
    ]

#%%

data_dir = 'test_search/nist/'
    
res_dir = 'test_search/est_results_nist/'


#%%
def split_comments(comment):
    ret = ''
    quote = False
    for c in comment:
        if c == ' ' and not quote:
            yield ret
            ret = ''
        elif c == '"':
            quote = not quote
        else:
            ret += c
            

#%%

def parse_msp(msplist):
    peaks = []
    item = {}
    for l in msplist:
        if not l:
            item['Peaks'] = peaks
            
            props = {k:v for k,v in map(lambda x: x.split('=', 1), split_comments(item['Comment']))}
            item['Props'] = props
#            print(len(peaks))
            yield item
            item = {}
            peaks = []
            continue
            
        if ': ' not in l:
            peak = l.split('\t')
    #        print(peak)
            peaks.append(peak)
            continue
    #        peaks.append()
        
        [k, v] = l.split(': ', 1)
    #    print(k,v)
        if not item:
            assert(k == 'Name')
        item[k] = v
    yield item
    

#%%

#%%


def get_first_psms(ss):
    prevspec = None
        
    for row in ss:
    #    print(row)
        
        if row['Protein'][0:3] == 'REV':
            continue
        
        ind = int(row['SpecID'].split('=')[1])
        if prevspec == ind:
            continue
        prevspec = ind
        
        qval = float(row['QValue'])
        if qval == 1:
            continue
        yield (ind, row['Peptide'], row['SpecEValue'])
#    break

def match_peptide(p_nist, p_msgf):
    i=0
    j=0
#    print(p_nist, p_msgf)
    if p_msgf[1] == '.':
        while p_msgf[j] != '.':
            j += 1
        j += 1
    while True:
#        print(p_nist[i])
        if p_nist[i] == '/':
            return True
        if j >= len(p_msgf):
            return False
        if p_msgf[j] in '-+.0123456789':
#            print(p_msgf[j], j, len(p_msgf))
            j += 1
            continue
        
        if p_nist[i] != p_msgf[j]:
            if p_nist[i] not in ['i', 'l'] or p_msgf[j] not in ['i', 'l']:
#                print(False, p_nist, p_msgf)
                return False
        
        i += 1
        j += 1
    
    return True



#%%

method_map = {
        '1S2D gamma & gaussian': '_1s2ca',
        '1S2D skew normal': '_1s2c',
        '2S3D skew normal': '_2s3c',
    }

def get_truefdr(species):
    species_dir = res_dir + species + '/'
    
    def get_peps(species):
        #mspfile = open('nist/human_consensus_final_true_lib.msp')
        mspfile = tarfile.open(data_dir+species+'_consensus_final_true_lib.tar.gz', 'r|gz')
        tarinfo = mspfile.next()
        mspfile = mspfile.extractfile(tarinfo)
        
        msplist = (l.decode("utf-8").rstrip() for l in mspfile)
        
        peps = []
        for item in parse_msp(msplist):
            if not item:
                continue
            peps.append(item['Name'])
        return peps
    
    peps = get_peps(species)
    
    def get_truefdr(species):
        f = open(data_dir+species+'_d.tsv')
        psmcsv = csv.DictReader(f, delimiter='\t')
        
        psms = get_first_psms(psmcsv)
        matches = []
        for spec, pep, score in psms:
        #    print(peps[spec], pep)
            matches.append((match_peptide(peps[spec], pep), score))
        #    print(match_peptide(peps[spec], pep))
            
        n = 0
        fc = 0
        qstart = 0
        qvals = np.zeros(len(matches))
        curv = []
        ncorr = 0
        nwrong = 0
        for m, score in matches:
        #    print(row)
            n += 1
            if not m:
                qval = fc / n
                curv.append((qval, n, score))
                qvals[qstart:n-1] = qval
                fc += 1
                qstart = n-1
                nwrong += 1
            else:
                ncorr += 1
            
            print(fc, n, fc/n)
        
        print('correct vs wrong', ncorr, nwrong)
        
        qval = fc / n
        qvals[qstart:n] = qval
        curv.append((qval, n, score))
        curv = np.array(curv, dtype=float)
        curv[:,2] = -np.log(curv[:,2])
        true_fdr = np.array(qvals)
        print(n)
    
#        true_thres = 0
#        for fdr,n,s in curv:
#            if fdr > 0.01:
#                break
#        #    nmatches = n
#            true_thres = s
        
#        ttfile = open(species_dir + 'true_thres_tda.txt', 'w')
#        ttfile.write("%f\n"%true_thres)
#        ttfile.close()
        
        return true_fdr
    
    true_fdr = get_truefdr(species)
    
    
    fdr_dir = species_dir + 'fdr/'
    truefdr_file = fdr_dir + 'true_tda.csv'
    
    np.savetxt(truefdr_file, true_fdr)
    
    return true_fdr
        
#%%
for species in species_list:
    get_truefdr(species)

