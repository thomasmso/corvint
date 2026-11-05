#import "AdManager.h"
#import <AppLovinSDK/AppLovinSDK.h>

static NSString *const kSdkKey = @"UZeET0n1kyJYiCe32G9DNDD-Jj2-wRFBwZZiQR4gpHO2kkmADDMl7Ch91_vZKPuBoMOceI0RP0XCwGhWM7hnzj";

@implementation AdManager

+ (instancetype)sharedManager
{
    static AdManager *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[AdManager alloc] init];
    });
    return shared;
}

- (void)initializeSdk
{
    ALSdkSettings *settings = [ALSdk shared].settings;
    settings.termsAndPrivacyPolicyFlowSettings.enabled = YES;
    settings.termsAndPrivacyPolicyFlowSettings.privacyPolicyURL = [NSURL URLWithString:@"https://puzzlequest.example.com/privacy"];
    settings.termsAndPrivacyPolicyFlowSettings.termsOfServiceURL = [NSURL URLWithString:@"https://puzzlequest.example.com/terms"];

    ALSdkInitializationConfiguration *initConfig = [ALSdkInitializationConfiguration configurationWithSdkKey:kSdkKey builderBlock:^(ALSdkInitializationConfigurationBuilder *builder) {
        builder.mediationProvider = ALMediationProviderMAX;
    }];

    [[ALSdk shared] initializeWithConfiguration:initConfig completionHandler:^(ALSdkConfiguration *sdkConfig) {
        // TODO: start loading ads
    }];
}

@end
