package com.example.project.backend.controllers;

import com.example.project.backend.entity.MaladeEnCharge;
import com.example.project.backend.services.MaladeEnChargeService.IMaladeEnChargeService;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/maladeEnCharge")
@CrossOrigin(origins = "http://localhost:4200/")
public class MaladeEnChargeController {
    private IMaladeEnChargeService maladeEnChargeService;

    @PostMapping("/add")
    public MaladeEnCharge addMaladeEnCharge(@RequestBody MaladeEnCharge maladeEnCharge) {
        return maladeEnChargeService.addMaladeEnCharge(maladeEnCharge);
    }

    @GetMapping("/retrieve-all")
    public List<MaladeEnCharge> retrieveAllMaladesEnCharge() {
        return maladeEnChargeService.retrieveAllMaladesEnCharge();
    }

    @GetMapping("/retrieve/{id}")
    public MaladeEnCharge retrieveMaladeEnCharge(@PathVariable("id") Long maladeEnChargeId) {
        return maladeEnChargeService.retrieveMaladeEnCharge(maladeEnChargeId);
    }

    @PutMapping("/modify")
    public MaladeEnCharge modifyMaladeEnCharge(@RequestBody MaladeEnCharge maladeEnCharge) {
        return maladeEnChargeService.updateMaladeEnCharge(maladeEnCharge);
    }

    @DeleteMapping("/remove/{id}")
    public void removeMaladeEnCharge(@PathVariable("id") Long maladeEnChargeId) {
        maladeEnChargeService.deleteMaladeEnCharge(maladeEnChargeId);
    }

}
