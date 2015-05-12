#include <time.h>

void saveAnalysis()
{
	time_t now = time(0);
	struct tm tstruct;
	char file[80];
	tstruct = *localtime(&now);
	strftime(file, sizeof(file), "Analysis_%Y-%m-%d_autosave.root", &tstruct);

	printf("Executing End-of-Run macro, saving analysis to %s\n", file);
	gUAN->SaveAll(file);
  	printf("Done.\n", file);

	exit(0);
}

void FinishMacro(Char_t* file = "ARHistograms.root")
{
	printf("\nEnd-of-Run macro executing:\n");
	TFile f(file, "recreate");
	if (!f) {
		printf("Open file %s for histogram save FAILED!!\n", file);
		exit(1);
	}
	gROOT->GetList()->Write();
	f.Close();
  	printf("All histograms saved to %s\n\n", file);

	exit(0);
}
