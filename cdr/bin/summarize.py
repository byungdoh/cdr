import argparse
import sys
import os
from cdr.config import Config
from cdr.util import load_cdr, filter_models, stderr

if __name__ == '__main__':

    argparser = argparse.ArgumentParser('''
        Generate summary of saved model(s)
    ''')
    argparser.add_argument('paths', nargs='+', help='Path(s) to config file(s) defining experiments')
    argparser.add_argument('-m', '--models', nargs='*', default = [], help='List of models for which to generate summaries. Regex permitted. If not, generates summaries for all CDR models.')
    argparser.add_argument('-r', '--random', action='store_true', help='Report random effects.')
    argparser.add_argument('-l', '--level', type=float, default = 95., help='Level (in percent) for any credible intervals (CDRBayes only).')
    argparser.add_argument('-n', '--nsamples', type=int, default = None, help='Number of MC samples to use for computing statistics (CDRBayes only). If unspecified, uses model default (**n_samples_eval** parameter).')
    argparser.add_argument('-t', '--timeunits', type=float, default = None, help='Number of time units over which to compute effect size integrals. If unspecified, uses longest timespan attested in training.')
    argparser.add_argument('-T', '--save_table', action='store_true', help='Save CSV table of model parameters.')
    argparser.add_argument('-p', '--prefix', type=str, default = None, help='String to prepend to output file.')
    args, unknown = argparser.parse_known_args()

    for path in args.paths:
        p = Config(path)

        if not p.use_gpu_if_available:
            os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

        models = filter_models(p.model_list, args.models, cdr_only=True)

        for m in models:

            stderr('Retrieving saved model %s...\n' % m)
            cdr_model = load_cdr(p.outdir + '/' + m)

            summary = cdr_model.summary(
                random=args.random,
                level=args.level,
                n_samples=args.nsamples,
                integral_n_time_units=args.timeunits
            )

            if args.prefix:
                outname = p.outdir + '/' + m + '/' + args.prefix + '_summary.txt'
            else:
                outname = p.outdir + '/' + m + '/summary.txt'

            stderr('Saving summary to %s' %outname)
            with open(outname, 'w') as f:
                f.write(summary)
            stderr(summary)

            if args.save_table:
                if args.prefix:
                    outname = p.outdir + '/' + m + '/' + args.prefix + '_cdr_parameters.csv'
                else:
                    outname = p.outdir + '/' + m + '/cdr_parameters.csv'

                cdr_model.save_parameter_table(level=args.level, n_samples=args.nsamples, outfile=outname)
                
                if args.prefix:
                    outname = p.outdir + '/' + m + '/' + args.prefix + '_cdr_irf_integrals.csv'
                else:
                    outname = p.outdir + '/' + m + '/cdr_irf_integrals.csv'

                cdr_model.save_irf_integral_table(level=args.level, n_samples=args.nsamples, outfile=outname)

            cdr_model.finalize()



