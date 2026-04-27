package com.example.project.backend.services.MaladeEnChargeService;

import com.example.project.backend.entity.MaladeEnCharge;

import java.util.List;

public interface IMaladeEnChargeService {

    List<MaladeEnCharge> retrieveAllMaladesEnCharge();
    MaladeEnCharge addMaladeEnCharge(MaladeEnCharge maladeEnCharge);
    void deleteMaladeEnCharge(Long id);
    MaladeEnCharge updateMaladeEnCharge(MaladeEnCharge maladeEnCharge);
    MaladeEnCharge retrieveMaladeEnCharge(Long id);

}
