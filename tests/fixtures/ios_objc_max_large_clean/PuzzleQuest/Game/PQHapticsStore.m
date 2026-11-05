#import "PQHapticsStore.h"

static NSString *const kKey = @"puzzlequest.haptics";

@implementation PQHapticsStore

+ (instancetype)sharedStore
{
    static PQHapticsStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQHapticsStore alloc] init];
    });
    return shared;
}

- (NSInteger)intensity
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setIntensity:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
