#import "PQSkinsStore.h"

static NSString *const kKey = @"puzzlequest.skins";

@implementation PQSkinsStore

+ (instancetype)sharedStore
{
    static PQSkinsStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQSkinsStore alloc] init];
    });
    return shared;
}

- (NSInteger)unlocked
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setUnlocked:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
