package com.example.project.backend.configurations;

import com.example.project.backend.entity.User;
import com.example.project.backend.repositories.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Component;

import java.util.Optional;

@Component
public class UserUserDetailsService implements UserDetailsService{
    @Autowired
    private UserRepository repository;

    @Override
    public UserDetails loadUserByUsername(String usernameOrEmail) throws UsernameNotFoundException {
        Optional<User> user = repository.findByUsername(usernameOrEmail);
        if (user.isEmpty()) {
            user = repository.findByEmail(usernameOrEmail);
        }
        return user.map(UserUserDetails::new)
                .orElseThrow(() -> new UsernameNotFoundException("user not found: " + usernameOrEmail));
    }
}
