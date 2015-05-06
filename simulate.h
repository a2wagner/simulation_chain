#ifndef _simulate_h_
#define _simulate_h_

inline double sgn(double x)
{
	if (x < 0) return -1;
	else if (x > 0) return 1;
	else return 0;
}

inline double thetaCrit()
{
	double E0 = 1.604;  // beam energy
	double me = 0.000510999;  // mass electron
	return me/E0;
}

inline double thetaCrit2()
{
	double thCr = thetaCrit();
	return thCr*thCr;
}

void simulate(Int_t events, Int_t output, const char* channel, const char* output_path);

void sim_etap_eeg(Int_t events, char* output);
void sim_etap_eeg_oldFF(Int_t events, char* output);
void sim_etap_eeg_FF1(Int_t events, char* output);
void sim_etap_etapipi(Int_t events, char* output);
void sim_etap_rho0g(Int_t events, char* output);
void sim_etap_mumug(Int_t events, char* output);
void sim_etap_gg(Int_t events, char* output);
void sim_eta_eeg(Int_t events, char* output);
void sim_eta_pipig(Int_t events, char* output);
void sim_eta_pipipi0(Int_t events, char* output);
void sim_eta_mumug(Int_t events, char* output);
void sim_eta_gg(Int_t events, char* output);
void sim_omega_eepi0(Int_t events, char* output);
void sim_omega_pipipi0(Int_t events, char* output);
void sim_omega_pipi(Int_t events, char* output);
void sim_rho0_ee(Int_t events, char* output);
void sim_rho0_pipi(Int_t events, char* output);
void sim_pi0_eeg(Int_t events, char* output);
void sim_pi0_gg(Int_t events, char* output);
void sim_pipi(Int_t events, char* output);
void sim_pipipi0(Int_t events, char* output);
void sim_pi0pi0_4g(Int_t events, char* output);
void sim_pi0eta_4g(Int_t events, char* output);

// new added channels for trigger condition tests and more

void sim_etap_pi0pi0eta(Int_t events, char* output);
void sim_etap_pi0pi0pi0(Int_t events, char* output);
void sim_etap_pipipi0(Int_t events, char* output);
void sim_etap_omegag(Int_t events, char* output);
void sim_omega_etag(Int_t events, char* output);

#endif //_simulate_h_

