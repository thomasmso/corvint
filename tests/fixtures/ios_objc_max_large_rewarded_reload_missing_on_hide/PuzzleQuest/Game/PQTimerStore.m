#import "PQTimerStore.h"

static NSString *const kKey = @"puzzlequest.timer";

@implementation PQTimerStore

+ (instancetype)sharedStore
{
    static PQTimerStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQTimerStore alloc] init];
    });
    return shared;
}

- (NSInteger)bestSeconds
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setBestSeconds:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
