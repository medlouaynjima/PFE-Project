package com.example.project.backend.services.MaladeEnChargeService;


import com.example.project.backend.entity.MaladeEnCharge;
import com.example.project.backend.repositories.MaladeEnChargeRepository;
import lombok.AllArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@AllArgsConstructor
public class MaladeEnChargeService implements IMaladeEnChargeService {


    MaladeEnChargeRepository maladeEnChargeRepository;

    @Override
    public List<MaladeEnCharge> retrieveAllMaladesEnCharge() {
        return maladeEnChargeRepository.findAll();
    }

    @Override
    public MaladeEnCharge addMaladeEnCharge(MaladeEnCharge maladeEnCharge) {
        maladeEnChargeRepository.save(maladeEnCharge);
        return maladeEnCharge;
    }

    @Override
    public void deleteMaladeEnCharge(Long id) {
        maladeEnChargeRepository.deleteById(id);
    }

    @Override
    public MaladeEnCharge updateMaladeEnCharge(MaladeEnCharge maladeEnCharge) {
        maladeEnChargeRepository.save(maladeEnCharge);
        return maladeEnCharge;
    }

    @Override
    public MaladeEnCharge retrieveMaladeEnCharge(Long id) {
        return maladeEnChargeRepository.findById(id).orElse(null);
    }
}
