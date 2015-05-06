#include "simulate.h"
#include <iostream>
#include <stdio.h>
#include <sstream>
#include <iomanip>  //to use setw and setfill
#include <string.h>
/*
#include "PReaction.h"
#include "PParticle.h"
#include "PBeamSmearing.h"
#include "PDecayManager.h"
#include "PDecayChannel.h"
#include "PSimpleVMDFF.h"
*/

void simulate(Int_t events, Int_t run, const char* channel, const char* output_path)
{
	gROOT->Reset();
	// properly initialise TRandom seed which is used by the smearing TF1 functions, independent of the Pluto random seed initialisation
	gRandom->SetSeed(0);

	// smear the beam
	PBeamSmearing *smear = new PBeamSmearing("beam_smear", "Beam Smearing");
	smear->SetReaction("g + p");  // define beam + target
	smear->SetMomentumFunction(new TF1("bremsstrahlung", "1./x", 1.45, 1.58));  // define function, here 1./x from 1.45 to 1.58 GeV [max possible energy in EPT is 1.577 GeV] (Pluto always calculate in GeV)
	smear->SetAngularSmearing(new TF1("angle", "x/(x*x + thetaCrit2())/(x*x + thetaCrit2())", 0., 5.*0.000510999/1.604));  // define the angular distribution of the bremsstrahlung spectrum (interval 0 to 5*theta_crit represents nearly the whole shape)
	makeDistributionManager()->Add(smear);  // add to Pluto

	// prepare output file name
	stringstream ss;
	ss << output_path << "/sim_" << channel << "_" << std::setw(2) << std::setfill('0') << run;
	std::string out;
	ss >> out;

	// choose the desired channel
	if (strstr(channel, "etap_") != NULL) {
		if (!strcmp(channel, "etap_e+e-g")) sim_etap_eeg(events, out.c_str());
		if (!strcmp(channel, "etap_e+e-g_oldFF")) sim_etap_eeg_oldFF(events, out.c_str());
		if (!strcmp(channel, "etap_e+e-g_FF1")) sim_etap_eeg_FF1(events, out.c_str());
		if (!strcmp(channel, "etap_pi+pi-eta")) sim_etap_pipieta(events, out.c_str());
		if (!strcmp(channel, "etap_rho0g")) sim_etap_rho0g(events, out.c_str());
		if (!strcmp(channel, "etap_mu+mu-g")) sim_etap_mumug(events, out.c_str());
		if (!strcmp(channel, "etap_gg")) sim_etap_gg(events, out.c_str());
		// new added channels
		if (!strcmp(channel, "etap_pi0pi0eta")) sim_etap_pi0pi0eta(events, out.c_str());
		if (!strcmp(channel, "etap_pi0pi0pi0")) sim_etap_pi0pi0pi0(events, out.c_str());
		if (!strcmp(channel, "etap_pi+pi-pi0")) sim_etap_pipipi0(events, out.c_str());
		if (!strcmp(channel, "etap_omegag")) sim_etap_omegag(events, out.c_str());
	}
	else if (strstr(channel, "eta_") != NULL) {
		if (!strcmp(channel, "eta_e+e-g")) sim_eta_eeg(events, out.c_str());
		if (!strcmp(channel, "eta_pi+pi-g")) sim_eta_pipig(events, out.c_str());
		if (!strcmp(channel, "eta_pi+pi-pi0")) sim_eta_pipipi0(events, out.c_str());
		if (!strcmp(channel, "eta_mu+mu-g")) sim_eta_mumug(events, out.c_str());
		if (!strcmp(channel, "pi0eta_4g")) sim_pi0eta_4g(events, out.c_str());
		if (!strcmp(channel, "eta_gg")) sim_eta_gg(events, out.c_str());
	}
	else if (strstr(channel, "omega_") != NULL) {
		if (!strcmp(channel, "omega_e+e-pi0")) sim_omega_eepi0(events, out.c_str());
		if (!strcmp(channel, "omega_pi+pi-pi0")) sim_omega_pipipi0(events, out.c_str());
		if (!strcmp(channel, "omega_pi+pi-")) sim_omega_pipi(events, out.c_str());
		// new added channel
		if (!strcmp(channel, "omega_etag")) sim_omega_etag(events, out.c_str());
	}
	else if (strstr(channel, "rho0_") != NULL) {
		if (!strcmp(channel, "rho0_e+e-")) sim_rho0_ee(events, out.c_str());
		if (!strcmp(channel, "rho0_pi+pi-")) sim_rho0_pipi(events, out.c_str());
	}
	else if (strstr(channel, "pi") != NULL) {
		if (!strcmp(channel, "pi0_e+e-g")) sim_pi0_eeg(events, out.c_str());
		if (!strcmp(channel, "pi0_gg")) sim_pi0_gg(events, out.c_str());
		if (!strcmp(channel, "pi+pi-")) sim_pipi(events, out.c_str());
		if (!strcmp(channel, "pi+pi-pi0")) sim_pipipi0(events, out.c_str());
		if (!strcmp(channel, "pi0pi0_4g")) sim_pi0pi0_4g(events, out.c_str());
	}
	else
		std::cout << "Error: Desired channel not found! Execution terminated." << std::endl;

	exit(0);
}

void sim_etap_eeg(Int_t events, char* output)
{
	// add the desired decay
	makeStaticData()->AddDecay("eta' Dalitz", "eta'", "dilepton,g", 0.0009);

	// change the form factor
	PSimpleVMDFF *ff = new PSimpleVMDFF("etaprime_ff@eta'_to_dilepton_g/formfactor", "Eta prime form factor", -1);
	// use another approximation with more realistic width instead of more or less a delta peak	like in the method with _oldFF
	ff->AddEquation("_ff2 = .5776*(.5776+.01)/((.5776-_q2)*(.5776-_q2)+.5776*.01)");  //equation from pluto paper page 11
	//ff->SetVectorMesonMass(0.77);
	makeDistributionManager()->Add(ff);

	// define the reaction as usual
	PReaction my_reaction(1.604, "g", "p", "p eta' [dilepton [e+ e-] g]", output, 1, 0, 0, 0);

	//my_reaction.Print();  // some infos about the reaction
	// start simulation
	my_reaction.Loop(events);
}

void sim_etap_eeg_oldFF(Int_t events, char* output)
{
	// add the desired decay
	makeStaticData()->AddDecay("eta' Dalitz", "eta'", "dilepton,g", 0.0009);

	// change the form factor
	PSimpleVMDFF *ff = new PSimpleVMDFF("etaprime_ff@eta'_to_dilepton_g/formfactor", "Eta prime form factor", -1);
	//use either the AddEquation or the SetVectorMesonMass version
	//ff->AddEquation("_ff2 = 1/(1 - _q2 / 0.767/0.767)/(1 - _q2 / 0.767/0.767) * (.5*(sgn(_q2- .9*.9) - sgn(_q2- .6*.6)) + 1)");  // letzter Faktor schließt die Polstelle bei 0.767 aus der Simulation aus
	ff->AddEquation("_ff2 = 1/(1 - _q2 / 0.767/0.767)/(1 - _q2 / 0.767/0.767); if(_ff2 > 100000.); _ff2 = 100000.;");  // Polstelle bändigen
	//ff->SetVectorMesonMass(0.77);
	makeDistributionManager()->Add(ff);

	// define the reaction as usual
	PReaction my_reaction(1.604, "g", "p", "p eta' [dilepton [e+ e-] g]", output, 1, 0, 0, 0);

	//my_reaction.Print();  // some infos about the reaction
	// start simulation
	my_reaction.Loop(events);
}

void sim_etap_eeg_FF1(Int_t events, char* output)
{
	printf("Processing eta' Dalitz decay with FF = 1 . . .\n");
	makeStaticData()->AddDecay("eta' Dalitz", "eta'", "dilepton,g", .0009);
	PSimpleVMDFF *ff = new PSimpleVMDFF("etaprime_ff@eta'_to_dilepton_g/formfactor", "Eta prime form factor", -1);
	ff->AddEquation("_ff2 = 1.");  // set FF to 1
	makeDistributionManager()->Add(ff);
	PReaction my_reaction(1.604, "g", "p", "p eta' [dilepton [e+ e-] g]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

void sim_etap_pipieta(Int_t events, char* output)
{
	PReaction my_reaction(1.604, "g", "p", "p eta' [eta [g g] pi+ pi-]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

void sim_etap_rho0g(Int_t events, char* output)
{
	PReaction my_reaction(1.604, "g", "p", "p eta' [rho0 [pi+ pi-] g]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
/*	PDecayManager *pdm = new PDecayManager;

	PParticle *beam   = new PParticle(1,1.604);     // beam (1.6 GeV Photon)
	PParticle *target = new PParticle(14);          // target (Proton)
	PParticle *s      = new PParticle(*beam + *target);

	PDecayChannel *c = new PDecayChannel;           // define reaction channels
	c->AddChannel(1.,"p","eta'");

	c_etap = new PDecayChannel;			// eta'
	c_etap->AddChannel(.294,"rho0","g");
	pdm->AddChannel("eta'",c_etap);

	c_rho = new PDecayChannel;			// rho0
	c_rho->AddChannel(4.7e-5,"e+","e-");
	c_rho->AddChannel(.99999,"pi+","pi-");
	pdm->AddChannel("rho0",c_rho);

	pdm->InitReaction(s,c);			// cocktail production in g + p
	//pdm->Print();				// print some information about the particle cocktail
	Int_t n = pdm->loop(100000,1,"test",1,0,1,0,1); // make events + vertices
	cout << "Events processed: " << n << endl;
*/
}

void sim_etap_mumug(Int_t events, char* output)
{
	PReaction my_reaction(1.604, "g", "p", "p eta' [dimuon [mu+ mu-] g]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

void sim_etap_gg(Int_t events, char* output)
{
	PReaction my_reaction(1.604, "g", "p", "p eta' [g g]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

void sim_eta_eeg(Int_t events, char* output){
	PReaction my_reaction(1.604, "g", "p", "p eta [dilepton [e+ e-] g]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

void sim_eta_pipig(Int_t events, char* output)
{
	PReaction my_reaction(1.604, "g", "p", "p eta [pi+ pi- g]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

void sim_eta_pipipi0(Int_t events, char* output)
{
	PReaction my_reaction(1.604, "g", "p", "p eta [pi+ pi- pi0 [g g]]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

void sim_eta_mumug(Int_t events, char* output)
{
	PReaction my_reaction(1.604, "g", "p", "p eta [dimuon [mu+ mu-] g]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

void sim_eta_gg(Int_t events, char* output)
{
	PReaction my_reaction(1.604, "g", "p", "p eta [g g]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

void sim_omega_eepi0(Int_t events, char* output)
{
	PReaction my_reaction(1.604, "g", "p", "p omega [dilepton [e+ e-] pi0 [g g]]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

void sim_omega_pipipi0(Int_t events, char* output)
{
	PReaction my_reaction(1.604, "g", "p", "p omega [pi+ pi- pi0 [g g]]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

void sim_omega_pipi(Int_t events, char* output)
{
	PReaction my_reaction(1.604, "g", "p", "p omega [pi+ pi-]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

void sim_rho0_ee(Int_t events, char* output)
{
	PReaction my_reaction(1.604, "g", "p", "p rho0 [e+ e-]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

void sim_rho0_pipi(Int_t events, char* output)
{
	PReaction my_reaction(1.604, "g", "p", "p rho0 [pi+ pi-]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

void sim_pi0_eeg(Int_t events, char* output)
{
	PReaction my_reaction(1.604, "g", "p", "p pi0 [dilepton [e+ e-] g]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

void sim_pi0_gg(Int_t events, char* output)
{
	PReaction my_reaction(1.604, "g", "p", "p pi0 [g g]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

void sim_pipi(Int_t events, char* output)
{
	PReaction my_reaction(1.604, "g", "p", "p pi+ pi-", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

void sim_pipipi0(Int_t events, char* output)
{
	PReaction my_reaction(1.604, "g", "p", "p pi+ pi- pi0 [g g]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

void sim_pi0pi0_4g(Int_t events, char* output)
{
	PReaction my_reaction(1.604, "g", "p", "p pi0 [g g] pi0 [g g]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

void sim_pi0eta_4g(Int_t events, char* output)
{
	PReaction my_reaction(1.604, "g", "p", "p pi0 [g g] eta [g g]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

// new added channels

void sim_etap_pi0pi0eta(Int_t events, char* output)
{
	PReaction my_reaction(1.604, "g", "p", "p eta' [eta [g g] pi0 [g g] pi0 [g g]]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

void sim_etap_pi0pi0pi0(Int_t events, char* output)
{
	PReaction my_reaction(1.604, "g", "p", "p eta' [pi0 [g g] pi0 [g g] pi0 [g g]]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

void sim_etap_pipipi0(Int_t events, char* output)
{
//TODO: implement channel eta' -> pi+ pi- pi0 properly
	makeStaticData()->AddDecay(-1, "eta' -> pi+ + pi- + pi0", "eta'", "pi+,pi-,pi0", .0036);
	PReaction my_reaction(1.604, "g", "p", "p eta' [pi+ pi- pi0 [g g]]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

void sim_etap_omegag(Int_t events, char* output)
{
//TODO: implement channel omega -> eta g properly
	//makeStaticData()->AddDecay(-1, "omega -> eta + gamma", "omega", "eta,g", .00046);
	//PReaction my_reaction(1.604, "g", "p", "p eta' [omega [eta [g g] g] g]", output, 1, 0, 0, 0);
	// main decay channel (89.2%)
	//PReaction my_reaction(1.604, "g", "p", "p eta' [omega [pi+ pi- pi0 [g g]] g]", output, 1, 0, 0, 0);
	// second main channel (8.28%)
	PReaction my_reaction(1.604, "g", "p", "p eta' [omega [pi0 [g g] g] g]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

void sim_omega_etag(Int_t events, char* output)
{
//TODO: implement channel omega -> eta g properly
	makeStaticData()->AddDecay(-1, "omega -> eta + gamma", "omega", "eta,g", .00046);
	PReaction my_reaction(1.604, "g", "p", "p omega [eta [g g] g]", output, 1, 0, 0, 0);
	my_reaction.Loop(events);
}

