#import "PQTutorialStore.h"

static NSString *const kKey = @"puzzlequest.tutorial";

@implementation PQTutorialStore

+ (instancetype)sharedStore
{
    static PQTutorialStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQTutorialStore alloc] init];
    });
    return shared;
}

- (NSInteger)step
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setStep:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
