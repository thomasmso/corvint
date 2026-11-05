#import "PQComboStore.h"

static NSString *const kKey = @"puzzlequest.combo";

@implementation PQComboStore

+ (instancetype)sharedStore
{
    static PQComboStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQComboStore alloc] init];
    });
    return shared;
}

- (NSInteger)best
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setBest:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
